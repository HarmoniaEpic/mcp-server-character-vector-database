"""
Gradio-based monitoring application
"""

import gradio as gr
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np

from config.logging import get_logger
from core.database import VectorDatabaseManager
from core.utils import safe_json_dumps, safe_json_loads
from .visualizers import (
    OscillationVisualizer,
    EntropyVisualizer,
    RelationshipVisualizer,
    SessionVisualizer,
)
from .themes import get_monitor_theme

logger = get_logger(__name__)


class MonitorApp:
    """Gradioベースのモニタリングアプリケーション"""
    
    def __init__(self, db_manager: Optional[VectorDatabaseManager] = None):
        """
        初期化
        
        Args:
            db_manager: データベースマネージャー（省略時は新規作成）
        """
        self.db = db_manager or VectorDatabaseManager()
        self.oscillation_viz = OscillationVisualizer()
        self.entropy_viz = EntropyVisualizer()
        self.relationship_viz = RelationshipVisualizer()
        self.session_viz = SessionVisualizer()
        
        self.app = None
        self._setup_interface()
    
    def _setup_interface(self):
        """Gradioインターフェースのセットアップ"""
        theme = get_monitor_theme()
        
        with gr.Blocks(
            title="MCP Server Monitor",
            theme=theme,
            css=self._get_custom_css()
        ) as self.app:
            gr.Markdown("# 🧠 MCP Server Character Vector Database Monitor")
            gr.Markdown("### Unified Inner Engine System v3.1 対応 - セキュアエントロピー統合版")
            
            with gr.Tabs():
                # ダッシュボードタブ
                with gr.TabItem("📊 ダッシュボード"):
                    self._setup_dashboard_tab()
                
                # セッション管理タブ
                with gr.TabItem("🔄 セッション管理"):
                    self._setup_session_tab()
                
                # キャラクター管理タブ
                with gr.TabItem("🎭 キャラクター管理"):
                    self._setup_character_tab()
                
                # 振動パターンタブ
                with gr.TabItem("📈 振動パターン"):
                    self._setup_oscillation_tab()
                
                # エントロピー監視タブ
                with gr.TabItem("🔐 セキュアエントロピー"):
                    self._setup_entropy_tab()
                
                # 関係性分析タブ
                with gr.TabItem("💫 関係性分析"):
                    self._setup_relationship_tab()
                
                # システム情報タブ
                with gr.TabItem("⚙️ システム情報"):
                    self._setup_system_tab()
            
            # 自動更新タイマー
            self.auto_refresh = gr.Timer(5.0)  # 5秒ごとに更新
    
    def _get_custom_css(self) -> str:
        """カスタムCSSを取得"""
        return """
        .gradio-container {
            font-family: 'Noto Sans JP', sans-serif;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .warning-box {
            background: #fee;
            border-left: 4px solid #f44336;
            padding: 10px;
            margin: 10px 0;
        }
        .success-box {
            background: #efe;
            border-left: 4px solid #4caf50;
            padding: 10px;
            margin: 10px 0;
        }
        """
    
    def _setup_dashboard_tab(self):
        """ダッシュボードタブのセットアップ"""
        with gr.Row():
            # システム状態カード
            with gr.Column(scale=1):
                gr.Markdown("### 🔄 システム状態")
                self.system_status = gr.JSON(label="システム状態")
            
            # アクティブセッション情報
            with gr.Column(scale=1):
                gr.Markdown("### 📍 アクティブセッション")
                self.active_session_info = gr.JSON(label="セッション情報")
            
            # 統計情報
            with gr.Column(scale=1):
                gr.Markdown("### 📊 統計情報")
                self.statistics = gr.JSON(label="統計")
        
        with gr.Row():
            # リアルタイムメトリクス
            self.metrics_plot = gr.Plot(label="リアルタイムメトリクス")
        
        # 更新ボタン
        refresh_btn = gr.Button("🔄 更新", variant="primary")
        refresh_btn.click(
            fn=self._update_dashboard,
            outputs=[
                self.system_status,
                self.active_session_info,
                self.statistics,
                self.metrics_plot
            ]
        )
        
        # 自動更新設定
        self.auto_refresh.tick(
            fn=self._update_dashboard,
            outputs=[
                self.system_status,
                self.active_session_info,
                self.statistics,
                self.metrics_plot
            ]
        )
    
    def _setup_session_tab(self):
        """セッション管理タブのセットアップ"""
        with gr.Row():
            # セッション一覧
            with gr.Column(scale=1):
                gr.Markdown("### 📋 セッション一覧")
                self.session_list = gr.Dataframe(
                    headers=["セッションID", "キャラクター", "開始時刻", "状態"],
                    label="セッション一覧"
                )
            
            # セッション詳細
            with gr.Column(scale=2):
                gr.Markdown("### 📝 セッション詳細")
                self.session_details = gr.JSON(label="詳細情報")
        
        with gr.Row():
            # セッション操作
            self.session_id_input = gr.Textbox(label="セッションID", placeholder="選択または入力")
            resume_btn = gr.Button("▶️ 再開", variant="primary")
            export_btn = gr.Button("💾 エクスポート")
            delete_btn = gr.Button("🗑️ 削除", variant="stop")
        
        # セッション振動履歴
        self.session_oscillation_plot = gr.Plot(label="セッション振動履歴")
        
        # イベントハンドラー
        self.session_list.select(
            fn=self._on_session_select,
            outputs=[self.session_id_input, self.session_details, self.session_oscillation_plot]
        )
        
        resume_btn.click(
            fn=self._resume_session,
            inputs=[self.session_id_input],
            outputs=[self.session_details]
        )
        
        export_btn.click(
            fn=self._export_session,
            inputs=[self.session_id_input],
            outputs=[gr.File(label="エクスポートファイル")]
        )
    
    def _setup_character_tab(self):
        """キャラクター管理タブのセットアップ"""
        with gr.Row():
            # キャラクター作成フォーム
            with gr.Column(scale=1):
                gr.Markdown("### ➕ キャラクター作成")
                char_name = gr.Textbox(label="名前")
                char_background = gr.Textbox(label="背景設定", lines=3)
                char_instruction = gr.Textbox(label="演技指導", lines=3)
                
                # Big5性格特性スライダー
                gr.Markdown("#### 性格特性 (Big5)")
                openness = gr.Slider(0, 1, 0.5, label="開放性")
                conscientiousness = gr.Slider(0, 1, 0.5, label="誠実性")
                extraversion = gr.Slider(0, 1, 0.5, label="外向性")
                agreeableness = gr.Slider(0, 1, 0.5, label="協調性")
                neuroticism = gr.Slider(0, 1, 0.5, label="神経症傾向")
                
                create_btn = gr.Button("🎭 作成", variant="primary")
            
            # キャラクター一覧と詳細
            with gr.Column(scale=2):
                gr.Markdown("### 📚 キャラクター一覧")
                self.character_list = gr.Dataframe(
                    headers=["ID", "名前", "作成日時"],
                    label="キャラクター一覧"
                )
                
                self.character_details = gr.JSON(label="キャラクター詳細")
                self.character_evolution_plot = gr.Plot(label="キャラクター進化")
        
        # イベントハンドラー
        create_btn.click(
            fn=self._create_character,
            inputs=[
                char_name, char_background, char_instruction,
                openness, conscientiousness, extraversion,
                agreeableness, neuroticism
            ],
            outputs=[self.character_list, self.character_details]
        )
    
    def _setup_oscillation_tab(self):
        """振動パターンタブのセットアップ"""
        with gr.Row():
            # 振動パターン設定
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ 振動パターン設定")
                osc_amplitude = gr.Slider(0, 1, 0.3, label="振幅")
                osc_frequency = gr.Slider(0, 2, 0.5, label="周波数")
                pink_noise_enabled = gr.Checkbox(True, label="1/fノイズ有効")
                pink_noise_intensity = gr.Slider(0, 0.5, 0.15, label="ノイズ強度")
                secure_entropy_enabled = gr.Checkbox(True, label="セキュアエントロピー有効")
                
                add_pattern_btn = gr.Button("📊 パターン追加")
            
            # 振動パターン可視化
            with gr.Column(scale=2):
                self.oscillation_realtime_plot = gr.Plot(label="リアルタイム振動パターン")
                self.oscillation_spectrum_plot = gr.Plot(label="周波数スペクトル")
        
        # メトリクス表示
        with gr.Row():
            self.oscillation_metrics = gr.JSON(label="振動メトリクス")
            calculate_metrics_btn = gr.Button("📐 メトリクス計算")
        
        # イベントハンドラー
        calculate_metrics_btn.click(
            fn=self._calculate_oscillation_metrics,
            outputs=[self.oscillation_metrics, self.oscillation_spectrum_plot]
        )
    
    def _setup_entropy_tab(self):
        """エントロピー監視タブのセットアップ"""
        with gr.Row():
            # エントロピー状態
            with gr.Column(scale=1):
                gr.Markdown("### 🔐 エントロピー源状態")
                self.entropy_status = gr.JSON(label="エントロピー品質")
                test_entropy_btn = gr.Button("🧪 エントロピーテスト")
            
            # エントロピー可視化
            with gr.Column(scale=2):
                self.entropy_distribution_plot = gr.Plot(label="エントロピー分布")
                self.entropy_quality_plot = gr.Plot(label="品質推移")
        
        # テスト結果
        self.entropy_test_results = gr.JSON(label="テスト結果")
        
        # イベントハンドラー
        test_entropy_btn.click(
            fn=self._test_entropy,
            outputs=[
                self.entropy_test_results,
                self.entropy_distribution_plot,
                self.entropy_quality_plot
            ]
        )
    
    def _setup_relationship_tab(self):
        """関係性分析タブのセットアップ"""
        with gr.Row():
            # 関係性パラメータ
            with gr.Column(scale=1):
                gr.Markdown("### 💫 関係性パラメータ")
                self.relationship_params = gr.JSON(label="現在のパラメータ")
                
                # 距離調整スライダー
                optimal_distance = gr.Slider(0, 1, 0.6, label="最適距離")
                attachment_level = gr.Slider(0, 1, 0.3, label="愛着レベル")
                dependency_risk = gr.Slider(0, 1, 0.2, label="依存リスク")
                
                update_relationship_btn = gr.Button("🔄 更新")
            
            # 関係性可視化
            with gr.Column(scale=2):
                self.relationship_distance_plot = gr.Plot(label="関係性距離推移")
                self.paradox_tension_plot = gr.Plot(label="二律背反の緊張")
        
        # 警告表示
        self.relationship_warnings = gr.Markdown("### ⚠️ 警告")
    
    def _setup_system_tab(self):
        """システム情報タブのセットアップ"""
        with gr.Row():
            # システム情報
            with gr.Column():
                gr.Markdown("### 🖥️ システム情報")
                self.system_info = gr.JSON(label="システム設定")
                self.db_stats = gr.JSON(label="データベース統計")
                self.performance_metrics = gr.JSON(label="パフォーマンス")
            
            # ログビューア
            with gr.Column():
                gr.Markdown("### 📜 システムログ")
                self.log_viewer = gr.Textbox(
                    label="ログ",
                    lines=20,
                    max_lines=50,
                    interactive=False
                )
                clear_log_btn = gr.Button("🧹 ログクリア")
        
        # データベース操作
        with gr.Row():
            backup_btn = gr.Button("💾 バックアップ")
            cleanup_btn = gr.Button("🧹 クリーンアップ")
            reset_btn = gr.Button("⚠️ リセット", variant="stop")
        
        # イベントハンドラー
        reset_btn.click(
            fn=self._reset_database,
            outputs=[self.system_info]
        )
    
    # === コールバック関数 ===
    
    def _update_dashboard(self) -> Tuple[Dict, Dict, Dict, go.Figure]:
        """ダッシュボードを更新"""
        try:
            # システム状態
            system_status = {
                "status": "稼働中",
                "uptime": "計測中",
                "version": "3.1.4",
                "secure_mode": True
            }
            
            # アクティブセッション
            session_info = {}
            if self.db.active_session_id:
                session_state = self.db.get_session_state()
                session_info = {
                    "session_id": self.db.active_session_id,
                    "character_id": self.db.active_character_id,
                    "interaction_count": session_state.get("interaction_count", 0),
                    "oscillation_samples": len(
                        self.db.oscillation_buffer.get(
                            self.db.active_session_id, {"values": []}
                        )["values"]
                    )
                }
            
            # 統計情報
            stats = self._get_system_statistics()
            
            # メトリクスプロット
            metrics_plot = self._create_metrics_plot()
            
            return system_status, session_info, stats, metrics_plot
            
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")
            return {}, {}, {}, go.Figure()
    
    def _get_system_statistics(self) -> Dict[str, Any]:
        """システム統計情報を取得"""
        stats = {
            "total_sessions": len(self.db.session_manager.list_sessions()),
            "active_sessions": len(self.db.session_manager.list_active_sessions()),
            "total_characters": 0,  # TODO: 実装
            "total_conversations": 0,  # TODO: 実装
            "entropy_quality": self.db.entropy_source.assess_entropy_quality().get("success_rate", 0)
        }
        return stats
    
    def _create_metrics_plot(self) -> go.Figure:
        """メトリクスプロットを作成"""
        fig = go.Figure()
        
        # 振動データがある場合
        if self.db.active_session_id and self.db.active_session_id in self.db.oscillation_buffer:
            buffer = self.db.oscillation_buffer[self.db.active_session_id]
            values = buffer["values"][-100:]  # 最新100点
            
            fig.add_trace(go.Scatter(
                y=values,
                mode='lines',
                name='振動パターン',
                line=dict(color='blue', width=2)
            ))
        
        fig.update_layout(
            title="リアルタイム振動パターン",
            xaxis_title="サンプル",
            yaxis_title="振幅",
            height=400
        )
        
        return fig
    
    def _on_session_select(self, evt: gr.SelectData) -> Tuple[str, Dict, go.Figure]:
        """セッション選択時の処理"""
        if evt.index is not None:
            # 選択されたセッションの情報を取得
            sessions = self.db.session_manager.list_sessions()
            if evt.index[0] < len(sessions):
                session_id = sessions[evt.index[0]]
                
                # セッション詳細を取得
                session_data = self.db.session_manager.load_session(session_id)
                
                # 振動履歴プロット
                oscillation_plot = self._create_session_oscillation_plot(session_id)
                
                return session_id, session_data, oscillation_plot
        
        return "", {}, go.Figure()
    
    def _create_session_oscillation_plot(self, session_id: str) -> go.Figure:
        """セッションの振動履歴プロットを作成"""
        fig = go.Figure()
        
        if session_id in self.db.oscillation_buffer:
            buffer = self.db.oscillation_buffer[session_id]
            values = buffer["values"]
            
            fig.add_trace(go.Scatter(
                y=values,
                mode='lines',
                name='振動履歴',
                line=dict(color='purple', width=1)
            ))
        
        fig.update_layout(
            title=f"セッション {session_id[:8]}... の振動履歴",
            xaxis_title="サンプル",
            yaxis_title="振幅",
            height=300
        )
        
        return fig
    
    def _resume_session(self, session_id: str) -> Dict:
        """セッションを再開"""
        try:
            success = self.db.resume_session(session_id)
            if success:
                return {"status": "success", "message": f"セッション {session_id} を再開しました"}
            else:
                return {"status": "error", "message": "セッションの再開に失敗しました"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _export_session(self, session_id: str) -> str:
        """セッションをエクスポート"""
        try:
            export_data = self.db.export_session_data(session_id)
            filename = f"session_export_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(safe_json_dumps(export_data, ensure_ascii=False, indent=2))
            
            return filename
        except Exception as e:
            logger.error(f"Export error: {e}")
            return ""
    
    def _create_character(
        self,
        name: str,
        background: str,
        instruction: str,
        openness: float,
        conscientiousness: float,
        extraversion: float,
        agreeableness: float,
        neuroticism: float
    ) -> Tuple[pd.DataFrame, Dict]:
        """キャラクターを作成"""
        try:
            character_id = self.db.add_character_profile(
                name=name,
                background=background,
                instruction=instruction,
                personality_traits={
                    "openness": openness,
                    "conscientiousness": conscientiousness,
                    "extraversion": extraversion,
                    "agreeableness": agreeableness,
                    "neuroticism": neuroticism
                },
                values={},
                goals=[],
                fears=[],
                existential_parameters={},
                engine_parameters={}
            )
            
            # キャラクター一覧を更新
            character_list = self._get_character_list()
            
            # 作成したキャラクターの詳細
            details = {
                "id": character_id,
                "name": name,
                "created": datetime.now().isoformat(),
                "status": "作成成功"
            }
            
            return character_list, details
            
        except Exception as e:
            logger.error(f"Character creation error: {e}")
            return pd.DataFrame(), {"error": str(e)}
    
    def _get_character_list(self) -> pd.DataFrame:
        """キャラクター一覧を取得"""
        # TODO: 実際のキャラクター一覧取得実装
        return pd.DataFrame(columns=["ID", "名前", "作成日時"])
    
    def _calculate_oscillation_metrics(self) -> Tuple[Dict, go.Figure]:
        """振動メトリクスを計算"""
        try:
            metrics = self.db.calculate_oscillation_metrics()
            
            # スペクトルプロット
            spectrum_plot = self._create_spectrum_plot(metrics)
            
            return metrics, spectrum_plot
            
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {"error": str(e)}, go.Figure()
    
    def _create_spectrum_plot(self, metrics: Dict) -> go.Figure:
        """周波数スペクトルプロットを作成"""
        fig = go.Figure()
        
        # TODO: 実際のスペクトルデータを使用
        fig.add_trace(go.Scatter(
            x=[0, 1, 2, 3, 4, 5],
            y=[1, 0.5, 0.33, 0.25, 0.2, 0.17],
            mode='lines+markers',
            name='1/f特性',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="周波数スペクトル",
            xaxis_title="周波数",
            yaxis_title="パワー",
            yaxis_type="log",
            height=400
        )
        
        return fig
    
    def _test_entropy(self) -> Tuple[Dict, go.Figure, go.Figure]:
        """エントロピーをテスト"""
        try:
            # エントロピーテスト実行
            test_samples = []
            for _ in range(100):
                entropy_val = self.db.entropy_source.get_secure_entropy(4)
                normalized = self.db.entropy_source.get_normalized_entropy()
                test_samples.append({
                    "raw": entropy_val,
                    "normalized": normalized
                })
            
            # 分布プロット
            distribution_plot = self._create_entropy_distribution_plot(test_samples)
            
            # 品質プロット
            quality_plot = self._create_entropy_quality_plot()
            
            # テスト結果
            results = {
                "sample_count": len(test_samples),
                "quality": self.db.entropy_source.assess_entropy_quality(),
                "timestamp": datetime.now().isoformat()
            }
            
            return results, distribution_plot, quality_plot
            
        except Exception as e:
            logger.error(f"Entropy test error: {e}")
            return {"error": str(e)}, go.Figure(), go.Figure()
    
    def _create_entropy_distribution_plot(self, samples: List[Dict]) -> go.Figure:
        """エントロピー分布プロットを作成"""
        normalized_values = [s["normalized"] for s in samples]
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=normalized_values,
            nbinsx=20,
            name='エントロピー分布'
        ))
        
        fig.update_layout(
            title="正規化エントロピー分布",
            xaxis_title="値",
            yaxis_title="頻度",
            height=400
        )
        
        return fig
    
    def _create_entropy_quality_plot(self) -> go.Figure:
        """エントロピー品質プロットを作成"""
        # TODO: 実際の品質履歴を使用
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(10)),
            y=[0.95 + np.random.uniform(-0.05, 0.05) for _ in range(10)],
            mode='lines+markers',
            name='成功率',
            line=dict(color='green', width=2)
        ))
        
        fig.update_layout(
            title="エントロピー品質推移",
            xaxis_title="時間",
            yaxis_title="成功率",
            yaxis_range=[0, 1],
            height=400
        )
        
        return fig
    
    def _reset_database(self) -> Dict:
        """データベースをリセット"""
        try:
            # 確認ダイアログが必要
            self.db.reset_database()
            return {"status": "success", "message": "データベースをリセットしました"}
        except Exception as e:
            logger.error(f"Reset error: {e}")
            return {"status": "error", "message": str(e)}
    
    def launch(self, **kwargs):
        """アプリケーションを起動"""
        return self.app.launch(**kwargs)
