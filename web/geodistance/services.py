import logging
from typing import Dict, Optional, Tuple
from opensearchpy import OpenSearch
from django.conf import settings


logger = logging.getLogger(__name__)


class GeoDistanceService:
    """
    OpenSearchを使用してgeo distance計算を行うサービスクラス
    arc（球面距離）とplain（平面距離）の両方を計算する
    """
    
    def __init__(self):
        """OpenSearchクライアントを初期化"""
        try:
            self.client = OpenSearch(
                hosts=[{
                    'host': settings.OPENSEARCH_HOST,
                    'port': settings.OPENSEARCH_PORT
                }],
                http_auth=(settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD),
                use_ssl=True,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                timeout=30
            )
            self.index_name = 'geo_distance_test'
        except Exception as e:
            logger.error(f"OpenSearchクライアントの初期化に失敗しました: {e}")
            self.client = None
    
    def _ensure_index_exists(self) -> bool:
        """テスト用のインデックスが存在することを確認し、なければ作成する"""
        try:
            if not self.client:
                return False
                
            if not self.client.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "location": {
                                "type": "geo_point"
                            },
                            "name": {
                                "type": "text"
                            }
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"インデックス '{self.index_name}' を作成しました")
            
            return True
        except Exception as e:
            logger.error(f"インデックスの作成に失敗しました: {e}")
            return False
    
    def _create_test_document(self, lat: float, lon: float, doc_id: str = "test_point") -> bool:
        """テスト用のドキュメントを作成"""
        try:
            if not self.client:
                return False
                
            doc = {
                "location": {
                    "lat": lat,
                    "lon": lon
                },
                "name": "test_point"
            }
            
            self.client.index(
                index=self.index_name,
                id=doc_id,
                body=doc,
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"テストドキュメントの作成に失敗しました: {e}")
            return False
    
    def calculate_distances(self, a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> Dict:
        """
        A地点とB地点間の距離をarc（球面距離）とplain（平面距離）で計算
        
        Args:
            a_lat: A地点の緯度
            a_lon: A地点の経度
            b_lat: B地点の緯度
            b_lon: B地点の経度
            
        Returns:
            Dict: 計算結果を含む辞書
        """
        result = {
            'success': False,
            'arc_distance_km': None,
            'plain_distance_km': None,
            'difference_km': None,
            'difference_percentage': None,
            'error_message': None
        }
        
        try:
            if not self.client:
                result['error_message'] = 'OpenSearchクライアントが初期化されていません'
                return result
            
            if not self._ensure_index_exists():
                result['error_message'] = 'インデックスの作成に失敗しました'
                return result
            
            if not self._create_test_document(a_lat, a_lon, "point_a"):
                result['error_message'] = 'テストドキュメントの作成に失敗しました'
                return result
            
            arc_distance = self._calculate_distance_with_type(b_lat, b_lon, "arc")
            if arc_distance is None:
                result['error_message'] = 'arc距離の計算に失敗しました'
                return result
            
            plain_distance = self._calculate_distance_with_type(b_lat, b_lon, "plane")
            if plain_distance is None:
                result['error_message'] = 'plain距離の計算に失敗しました'
                return result
            
            difference = abs(arc_distance - plain_distance)
            difference_percentage = (difference / arc_distance * 100) if arc_distance > 0 else 0
            
            result.update({
                'success': True,
                'arc_distance_km': round(arc_distance, 3),
                'plain_distance_km': round(plain_distance, 3),
                'difference_km': round(difference, 3),
                'difference_percentage': round(difference_percentage, 2)
            })
            
        except Exception as e:
            logger.error(f"距離計算中にエラーが発生しました: {e}")
            result['error_message'] = f'計算エラー: {str(e)}'
        
        return result
    
    def _calculate_distance_with_type(self, target_lat: float, target_lon: float, distance_type: str) -> Optional[float]:
        """
        指定された距離タイプで距離を計算
        
        Args:
            target_lat: 目標地点の緯度
            target_lon: 目標地点の経度
            distance_type: "arc" または "plane"
            
        Returns:
            Optional[float]: 距離（km）、エラーの場合はNone
        """
        try:
            query = {
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {
                        "_geo_distance": {
                            "location": {
                                "lat": target_lat,
                                "lon": target_lon
                            },
                            "order": "asc",
                            "unit": "km",
                            "distance_type": distance_type
                        }
                    }
                ]
            }
            
            response = self.client.search(
                index=self.index_name,
                body=query,
                size=1
            )
            
            if response['hits']['total']['value'] > 0:
                hit = response['hits']['hits'][0]
                distance = hit['sort'][0]
                return float(distance)
            
            return None
            
        except Exception as e:
            logger.error(f"距離計算クエリでエラーが発生しました: {e}")
            return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        OpenSearch接続をテスト
        
        Returns:
            Tuple[bool, str]: (接続成功フラグ, メッセージ)
        """
        try:
            if not self.client:
                return False, "OpenSearchクライアントが初期化されていません"
            
            health = self.client.cluster.health()
            return True, f"接続成功: クラスター状態 = {health['status']}"
            
        except Exception as e:
            return False, f"接続エラー: {str(e)}"
