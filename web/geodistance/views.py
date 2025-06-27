from django.shortcuts import render
from django.contrib import messages
from .forms import GeoDistanceForm
from .services import GeoDistanceService


def geo_distance_view(request):
    """
    緯度経度入力フォームを表示し、OpenSearchでgeo distance計算を実行するビュー
    """
    if request.method == 'POST':
        form = GeoDistanceForm(request.POST)
        if form.is_valid():
            a_lat = form.cleaned_data['a_latitude']
            a_lon = form.cleaned_data['a_longitude']
            b_lat = form.cleaned_data['b_latitude']
            b_lon = form.cleaned_data['b_longitude']
            
            service = GeoDistanceService()
            distances = service.calculate_distances(a_lat, a_lon, b_lat, b_lon)
            
            if distances['success']:
                context = {
                    'form': form,
                    'distances': distances,
                    'a_point': {'lat': a_lat, 'lon': a_lon},
                    'b_point': {'lat': b_lat, 'lon': b_lon}
                }
                return render(request, 'geodistance/result.html', context)
            else:
                messages.error(request, f'距離計算でエラーが発生しました: {distances["error_message"]}')
        else:
            messages.error(request, 'フォームの入力内容に問題があります。正しい値を入力してください。')
    else:
        form = GeoDistanceForm()
    
    return render(request, 'geodistance/form.html', {'form': form})
