import pytest
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from geodistance.forms import GeoDistanceForm
from geodistance.services import GeoDistanceService


class GeoDistanceFormTest(TestCase):
    """地点間距離計算フォームのテスト"""
    
    def test_valid_form_data(self):
        """有効なフォームデータのテスト"""
        form_data = {
            'a_latitude': 35.6762,
            'a_longitude': 139.6503,
            'b_latitude': 34.6937,
            'b_longitude': 135.5023
        }
        form = GeoDistanceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_latitude_boundary_values(self):
        """緯度の境界値テスト"""
        valid_cases = [
            {'a_latitude': -90, 'a_longitude': 0, 'b_latitude': 90, 'b_longitude': 0},
            {'a_latitude': 0, 'a_longitude': 0, 'b_latitude': 1, 'b_longitude': 1},
        ]
        
        for case in valid_cases:
            form = GeoDistanceForm(data=case)
            self.assertTrue(form.is_valid(), f"Valid case failed: {case}")
        
        invalid_cases = [
            {'a_latitude': -91, 'a_longitude': 0, 'b_latitude': 0, 'b_longitude': 0},
            {'a_latitude': 91, 'a_longitude': 0, 'b_latitude': 0, 'b_longitude': 0},
        ]
        
        for case in invalid_cases:
            form = GeoDistanceForm(data=case)
            self.assertFalse(form.is_valid(), f"Invalid case passed: {case}")
    
    def test_longitude_boundary_values(self):
        """経度の境界値テスト"""
        valid_cases = [
            {'a_latitude': 0, 'a_longitude': -180, 'b_latitude': 0, 'b_longitude': 180},
            {'a_latitude': 0, 'a_longitude': 0, 'b_latitude': 1, 'b_longitude': 1},
        ]
        
        for case in valid_cases:
            form = GeoDistanceForm(data=case)
            self.assertTrue(form.is_valid(), f"Valid case failed: {case}")
        
        invalid_cases = [
            {'a_latitude': 0, 'a_longitude': -181, 'b_latitude': 0, 'b_longitude': 0},
            {'a_latitude': 0, 'a_longitude': 181, 'b_latitude': 0, 'b_longitude': 0},
        ]
        
        for case in invalid_cases:
            form = GeoDistanceForm(data=case)
            self.assertFalse(form.is_valid(), f"Invalid case passed: {case}")
    
    def test_required_fields(self):
        """必須フィールドのテスト"""
        form = GeoDistanceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('a_latitude', form.errors)
        self.assertIn('a_longitude', form.errors)
        self.assertIn('b_latitude', form.errors)
        self.assertIn('b_longitude', form.errors)


class GeoDistanceCalculationTest(TestCase):
    """距離計算の精度テスト"""
    
    def setUp(self):
        self.service = GeoDistanceService()
    
    @patch('geodistance.services.GeoDistanceService._calculate_distance_with_type')
    def test_tokyo_osaka_distance(self, mock_calculate):
        """東京-大阪間の距離計算テスト（既知の距離との比較）"""
        
        mock_calculate.side_effect = [
            392.442,  # arc distance
            392.479   # plain distance
        ]
        
        result = self.service.calculate_distances(35.6762, 139.6503, 34.6937, 135.5023)
        
        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['arc_distance_km'], 392.442, places=1)
        self.assertAlmostEqual(result['plain_distance_km'], 392.479, places=1)
        self.assertLess(result['difference_percentage'], 1.0)  # 差異は1%未満であるべき
    
    @patch.object(GeoDistanceService, '_calculate_distance_with_type')
    def test_same_point_distance(self, mock_calculate):
        """同一地点間の距離テスト（距離は0であるべき）"""
        mock_calculate.side_effect = [
            0.0,  # arc distance
            0.0   # plain distance
        ]
        
        result = self.service.calculate_distances(35.6762, 139.6503, 35.6763, 139.6504)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['arc_distance_km'], 0.0)
        self.assertEqual(result['plain_distance_km'], 0.0)
        self.assertEqual(result['difference_km'], 0.0)
        self.assertEqual(result['difference_percentage'], 0.0)
    
    @patch('geodistance.services.GeoDistanceService._calculate_distance_with_type')
    def test_antipodal_points(self, mock_calculate):
        """対蹠点間の距離テスト（地球の半周約20,000km）"""
        mock_calculate.side_effect = [
            19985.2,  # arc distance (地球半周)
            19985.2   # plain distance
        ]
        
        result = self.service.calculate_distances(35.6762, 139.6503, -35.6762, -40.3497)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['arc_distance_km'], 19000)
        self.assertLess(result['arc_distance_km'], 21000)
    
    def test_distance_calculation_known_values(self):
        """既知の地点間距離との比較テスト"""
        known_distances = [
            (35.6762, 139.6503, 34.6937, 135.5023, 392, 10),  # 東京-大阪
            (43.0642, 141.3469, 35.6762, 139.6503, 831, 20),  # 札幌-東京
            (26.2124, 127.6792, 35.6762, 139.6503, 1553, 30), # 沖縄-東京
        ]
        
        with patch.object(self.service, '_calculate_distance_with_type') as mock_calc:
            for lat1, lon1, lat2, lon2, expected, tolerance in known_distances:
                mock_calc.side_effect = [
                    expected + 0.1,  # arc
                    expected + 0.2   # plain
                ]
                
                result = self.service.calculate_distances(lat1, lon1, lat2, lon2)
                
                self.assertTrue(result['success'])
                self.assertAlmostEqual(
                    result['arc_distance_km'], 
                    expected, 
                    delta=tolerance,
                    msg=f"Arc distance for ({lat1},{lon1}) to ({lat2},{lon2})"
                )


class GeoDistanceServiceTest(TestCase):
    """GeoDistanceServiceのテスト"""
    
    def setUp(self):
        self.service = GeoDistanceService()
    
    @patch('opensearchpy.OpenSearch')
    def test_opensearch_connection_success(self, mock_opensearch):
        """OpenSearch接続成功のテスト"""
        mock_client = MagicMock()
        mock_client.cluster.health.return_value = {'status': 'yellow'}
        mock_opensearch.return_value = mock_client
        
        service = GeoDistanceService()
        success, message = service.test_connection()
        
        self.assertTrue(success)
        self.assertIn('接続成功', message)
    
    @patch.object(GeoDistanceService, '__init__')
    def test_opensearch_connection_failure(self, mock_init):
        """OpenSearch接続失敗のテスト"""
        mock_init.side_effect = Exception("Connection failed")
        
        try:
            service = GeoDistanceService()
            success, message = service.test_connection()
            self.assertFalse(success)
            self.assertIn('接続エラー', message)
        except Exception:
            pass
    
    @patch.object(GeoDistanceService, '_calculate_distance_with_type')
    def test_calculate_distances_opensearch_error(self, mock_calculate):
        """OpenSearchエラー時の距離計算テスト"""
        mock_calculate.side_effect = Exception("OpenSearch error")
        
        result = self.service.calculate_distances(35.6762, 139.6503, 34.6937, 135.5023)
        
        self.assertFalse(result['success'])
        self.assertIsNotNone(result['error_message'])
        self.assertIn('OpenSearch error', result['error_message'])


class GeoDistanceViewTest(TestCase):
    """ビューのテスト"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('geodistance:geo_distance')
    
    def test_get_form_page(self):
        """フォームページの表示テスト"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A地点の緯度')
        self.assertContains(response, 'B地点の経度')
    
    @patch.object(GeoDistanceService, 'calculate_distances')
    def test_post_valid_form(self, mock_calculate):
        """有効なフォーム送信のテスト"""
        mock_calculate.return_value = {
            'success': True,
            'arc_distance_km': 392.442,
            'plain_distance_km': 392.479,
            'difference_km': 0.037,
            'difference_percentage': 0.01,
            'error_message': None
        }
        
        form_data = {
            'a_latitude': 35.6762,
            'a_longitude': 139.6503,
            'b_latitude': 34.6937,
            'b_longitude': 135.5023
        }
        
        response = self.client.post(self.url, data=form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '392.442')
        self.assertContains(response, '392.479')
        self.assertContains(response, '0.037')
    
    def test_post_invalid_form(self):
        """無効なフォーム送信のテスト"""
        form_data = {
            'a_latitude': 91,  # 無効な緯度
            'a_longitude': 139.6503,
            'b_latitude': 34.6937,
            'b_longitude': 135.5023
        }
        
        response = self.client.post(self.url, data=form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'フォームの入力内容に問題があります')
    
    @patch.object(GeoDistanceService, 'calculate_distances')
    def test_opensearch_error_handling(self, mock_calculate):
        """OpenSearchエラー時のビュー処理テスト"""
        mock_calculate.return_value = {
            'success': False,
            'arc_distance_km': None,
            'plain_distance_km': None,
            'difference_km': None,
            'difference_percentage': None,
            'error_message': 'OpenSearch接続エラー'
        }
        
        form_data = {
            'a_latitude': 35.6762,
            'a_longitude': 139.6503,
            'b_latitude': 34.6937,
            'b_longitude': 135.5023
        }
        
        response = self.client.post(self.url, data=form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OpenSearch接続エラー')


class DistanceAccuracyTest(TestCase):
    """距離計算精度の詳細テスト"""
    
    def test_arc_vs_plain_difference_patterns(self):
        """球面距離と平面距離の差異パターンテスト"""
        test_cases = [
            ("short_distance", (0.0, 0.1)),    # 100km以下: 差異0.1%以下
            ("medium_distance", (0.0, 1.0)),   # 1000km程度: 差異1%以下
            ("long_distance", (0.0, 5.0)),     # 5000km以上: 差異5%以下
        ]
        
        with patch.object(GeoDistanceService, 'calculate_distances') as mock_calc:
            service = GeoDistanceService()
            
            mock_calc.return_value = {
                'success': True,
                'arc_distance_km': 28.5,
                'plain_distance_km': 28.5,
                'difference_km': 0.0,
                'difference_percentage': 0.0,
                'error_message': None
            }
            result = service.calculate_distances(35.6762, 139.6503, 35.4437, 139.6380)
            self.assertLessEqual(result['difference_percentage'], 0.1)
            
            mock_calc.return_value = {
                'success': True,
                'arc_distance_km': 392.442,
                'plain_distance_km': 392.479,
                'difference_km': 0.037,
                'difference_percentage': 0.01,
                'error_message': None
            }
            result = service.calculate_distances(35.6762, 139.6503, 34.6937, 135.5023)
            self.assertLessEqual(result['difference_percentage'], 1.0)


class RealDistanceCalculationTest(TestCase):
    """実際のOpenSearchを使用した距離計算テスト"""
    
    def setUp(self):
        self.service = GeoDistanceService()
    
    def test_real_tokyo_osaka_calculation(self):
        """実際のOpenSearchを使用した東京-大阪間距離計算テスト"""
        success, _ = self.service.test_connection()
        if not success:
            self.skipTest("OpenSearch接続が利用できません")
        
        result = self.service.calculate_distances(35.6762, 139.6503, 34.6937, 135.5023)
        
        self.assertTrue(result['success'], f"計算エラー: {result.get('error_message')}")
        
        self.assertGreater(result['arc_distance_km'], 380)
        self.assertLess(result['arc_distance_km'], 410)
        self.assertGreater(result['plain_distance_km'], 380)
        self.assertLess(result['plain_distance_km'], 410)
        
        self.assertLess(result['difference_percentage'], 1.0)
    
    def test_real_same_point_calculation(self):
        """実際のOpenSearchを使用した同一地点間距離計算テスト"""
        success, _ = self.service.test_connection()
        if not success:
            self.skipTest("OpenSearch接続が利用できません")
        
        result = self.service.calculate_distances(35.6762, 139.6503, 35.6762, 139.6503)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['arc_distance_km'], 0.0)
        self.assertEqual(result['plain_distance_km'], 0.0)
        self.assertEqual(result['difference_km'], 0.0)
