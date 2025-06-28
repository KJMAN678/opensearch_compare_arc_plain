from django import forms


class GeoDistanceForm(forms.Form):
    a_latitude = forms.FloatField(
        label="A地点の緯度",
        min_value=-90,
        max_value=90,
        widget=forms.NumberInput(
            attrs={
                "step": "0.001",
                "placeholder": "例: 35.6762",
                "class": "form-control",
            }
        ),
        help_text="緯度は-90度から90度の範囲で入力してください",
    )
    a_longitude = forms.FloatField(
        label="A地点の経度",
        min_value=-180,
        max_value=180,
        widget=forms.NumberInput(
            attrs={
                "step": "0.001",
                "placeholder": "例: 139.6503",
                "class": "form-control",
            }
        ),
        help_text="経度は-180度から180度の範囲で入力してください",
    )
    b_latitude = forms.FloatField(
        label="B地点の緯度",
        min_value=-90,
        max_value=90,
        widget=forms.NumberInput(
            attrs={
                "step": "0.001",
                "placeholder": "例: 34.6937",
                "class": "form-control",
            }
        ),
        help_text="緯度は-90度から90度の範囲で入力してください",
    )
    b_longitude = forms.FloatField(
        label="B地点の経度",
        min_value=-180,
        max_value=180,
        widget=forms.NumberInput(
            attrs={
                "step": "0.001",
                "placeholder": "例: 135.5023",
                "class": "form-control",
            }
        ),
        help_text="経度は-180度から180度の範囲で入力してください",
    )

    def clean(self):
        cleaned_data = super().clean()
        a_lat = cleaned_data.get("a_latitude")
        a_lon = cleaned_data.get("a_longitude")
        b_lat = cleaned_data.get("b_latitude")
        b_lon = cleaned_data.get("b_longitude")

        if (
            a_lat is not None
            and a_lon is not None
            and b_lat is not None
            and b_lon is not None
        ):
            # 浮動小数点数の精度問題を考慮した比較（許容誤差: 0.0001度 = 約11メートル）
            tolerance = 0.0001
            if abs(a_lat - b_lat) < tolerance and abs(a_lon - b_lon) < tolerance:
                raise forms.ValidationError(
                    "A地点とB地点が同じ座標です。異なる座標を入力してください。"
                )

        return cleaned_data
