"""
Data visualization components
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class OscillationVisualizer:
    """振動パターン可視化"""
    
    def create_realtime_plot(self, values: List[float], 
                            timestamps: Optional[List[datetime]] = None) -> go.Figure:
        """リアルタイム振動プロット"""
        fig = go.Figure()
        
        if timestamps:
            x_data = timestamps
        else:
            x_data = list(range(len(values)))
        
        # メインの振動パターン
        fig.add_trace(go.Scatter(
            x=x_data,
            y=values,
            mode='lines',
            name='振動パターン',
            line=dict(color='blue', width=2)
        ))
        
        # 移動平均
        if len(values) > 10:
            window_size = min(10, len(values) // 5)
            moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')
            fig.add_trace(go.Scatter(
                x=x_data[window_size-1:],
                y=moving_avg,
                mode='lines',
                name='移動平均',
                line=dict(color='red', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title="リアルタイム振動パターン",
            xaxis_title="時間" if timestamps else "サンプル",
            yaxis_title="振幅",
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_phase_space_plot(self, values: List[float]) -> go.Figure:
        """位相空間プロット"""
        if len(values) < 2:
            return go.Figure()
        
        fig = go.Figure()
        
        # 位相空間 (x(t) vs x(t+1))
        fig.add_trace(go.Scatter(
            x=values[:-1],
            y=values[1:],
            mode='markers+lines',
            name='位相軌道',
            marker=dict(
                size=5,
                color=list(range(len(values)-1)),
                colorscale='Viridis',
                showscale=True
            ),
            line=dict(width=1, color='rgba(0,0,0,0.3)')
        ))
        
        fig.update_layout(
            title="位相空間プロット",
            xaxis_title="x(t)",
            yaxis_title="x(t+1)",
            height=400
        )
        
        return fig
    
    def create_spectrum_analysis(self, values: List[float]) -> go.Figure:
        """周波数スペクトル解析"""
        if len(values) < 8:
            return go.Figure()
        
        fig = go.Figure()
        
        # FFT計算
        fft = np.fft.fft(values)
        frequencies = np.fft.fftfreq(len(values))
        power_spectrum = np.abs(fft) ** 2
        
        # 正の周波数のみ
        positive_freq_idx = frequencies > 0
        positive_freqs = frequencies[positive_freq_idx]
        positive_power = power_spectrum[positive_freq_idx]
        
        # パワースペクトル
        fig.add_trace(go.Scatter(
            x=positive_freqs,
            y=positive_power,
            mode='lines',
            name='パワースペクトル',
            line=dict(color='purple', width=2)
        ))
        
        # 1/fフィッティング
        if len(positive_freqs) > 10:
            log_freq = np.log10(positive_freqs + 1e-10)
            log_power = np.log10(positive_power + 1e-10)
            valid_idx = np.isfinite(log_freq) & np.isfinite(log_power)
            
            if np.any(valid_idx):
                slope, intercept = np.polyfit(log_freq[valid_idx], log_power[valid_idx], 1)
                fit_power = 10 ** (slope * log_freq + intercept)
                
                fig.add_trace(go.Scatter(
                    x=positive_freqs,
                    y=fit_power,
                    mode='lines',
                    name=f'1/f^{-slope:.2f}',
                    line=dict(color='red', width=1, dash='dash')
                ))
        
        fig.update_layout(
            title="周波数スペクトル解析",
            xaxis_title="周波数",
            yaxis_title="パワー",
            xaxis_type="log",
            yaxis_type="log",
            height=400
        )
        
        return fig


class EntropyVisualizer:
    """エントロピー可視化"""
    
    def create_entropy_heatmap(self, entropy_history: List[Dict[str, Any]]) -> go.Figure:
        """エントロピーヒートマップ"""
        # データを時間ごとに整理
        time_bins = 60  # 60秒ごと
        heatmap_data = []
        
        # TODO: 実装
        
        fig = go.Figure(data=go.Heatmap(
            z=[[0.9, 0.8, 0.95], [0.85, 0.9, 0.88], [0.92, 0.87, 0.9]],
            text=[["高", "中", "高"], ["中", "高", "高"], ["高", "高", "高"]],
            texttemplate="%{text}",
            colorscale='RdYlGn'
        ))
        
        fig.update_layout(
            title="エントロピー品質ヒートマップ",
            xaxis_title="時間",
            yaxis_title="エントロピー源",
            height=400
        )
        
        return fig
    
    def create_entropy_sources_plot(self, quality_data: Dict[str, Any]) -> go.Figure:
        """エントロピー源の状態"""
        sources = quality_data.get("entropy_sources", [])
        
        fig = go.Figure()
        
        # 各エントロピー源の寄与度
        fig.add_trace(go.Bar(
            x=sources,
            y=[0.2] * len(sources),  # TODO: 実際の寄与度
            name='寄与度',
            marker_color=['green' if 'secure' in s else 'blue' for s in sources]
        ))
        
        fig.update_layout(
            title="エントロピー源の寄与度",
            xaxis_title="エントロピー源",
            yaxis_title="寄与度",
            height=400
        )
        
        return fig


class RelationshipVisualizer:
    """関係性可視化"""
    
    def create_distance_plot(self, history: List[Dict[str, Any]]) -> go.Figure:
        """関係性距離の推移"""
        fig = go.Figure()
        
        # TODO: 実際の履歴データを使用
        x = list(range(50))
        optimal = [0.6] * 50
        current = [0.6 + 0.1 * np.sin(i/5) for i in x]
        
        fig.add_trace(go.Scatter(
            x=x,
            y=optimal,
            mode='lines',
            name='最適距離',
            line=dict(color='green', width=2, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=x,
            y=current,
            mode='lines',
            name='現在の距離',
            line=dict(color='blue', width=2)
        ))
        
        # 危険領域
        fig.add_hrect(y0=0, y1=0.3, 
                     fillcolor="red", opacity=0.1,
                     annotation_text="依存リスク", annotation_position="top left")
        fig.add_hrect(y0=0.8, y1=1.0, 
                     fillcolor="orange", opacity=0.1,
                     annotation_text="疎遠リスク", annotation_position="bottom left")
        
        fig.update_layout(
            title="関係性距離の推移",
            xaxis_title="時間",
            yaxis_title="距離",
            yaxis_range=[0, 1],
            height=400
        )
        
        return fig
    
    def create_paradox_tension_plot(self, tension_history: List[float]) -> go.Figure:
        """二律背反の緊張度"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            y=tension_history,
            mode='lines',
            fill='tozeroy',
            name='緊張度',
            line=dict(color='purple', width=2)
        ))
        
        # 警告レベル
        fig.add_hline(y=0.7, line_dash="dash", line_color="red",
                     annotation_text="高緊張")
        
        fig.update_layout(
            title="二律背反の緊張度",
            xaxis_title="時間",
            yaxis_title="緊張度",
            yaxis_range=[0, 1],
            height=400
        )
        
        return fig


class SessionVisualizer:
    """セッション可視化"""
    
    def create_session_timeline(self, sessions: List[Dict[str, Any]]) -> go.Figure:
        """セッションタイムライン"""
        fig = go.Figure()
        
        # TODO: 実際のセッションデータを使用
        for i, session in enumerate(sessions[:10]):  # 最新10件
            start = datetime.now() - timedelta(hours=i*2)
            end = start + timedelta(hours=1)
            
            fig.add_trace(go.Scatter(
                x=[start, end],
                y=[i, i],
                mode='lines+markers',
                name=f"Session {i}",
                line=dict(width=10),
                marker=dict(size=10)
            ))
        
        fig.update_layout(
            title="セッションタイムライン",
            xaxis_title="時間",
            yaxis_title="セッション",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_interaction_heatmap(self, interaction_data: Dict[str, Any]) -> go.Figure:
        """インタラクションヒートマップ"""
        # TODO: 実装
        days = ['月', '火', '水', '木', '金', '土', '日']
        hours = list(range(24))
        
        # ダミーデータ
        z = np.random.randint(0, 10, size=(7, 24))
        
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=hours,
            y=days,
            colorscale='Blues'
        ))
        
        fig.update_layout(
            title="インタラクション頻度",
            xaxis_title="時間",
            yaxis_title="曜日",
            height=400
        )
        
        return fig
