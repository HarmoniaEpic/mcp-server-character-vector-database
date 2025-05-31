"""
MCP tool definitions
"""

from typing import List
from mcp.types import Tool


def get_tool_definitions() -> List[Tool]:
    """Get all tool definitions"""
    return [
        # Session management tools
        Tool(
            name="start_session",
            description="新しいセッションを開始",
            inputSchema={
                "type": "object",
                "properties": {
                    "character_id": {"type": "string", "description": "キャラクターID"}
                },
                "required": ["character_id"]
            }
        ),
        Tool(
            name="resume_session",
            description="既存のセッションを再開",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "セッションID"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="get_session_state",
            description="セッションの現在の状態を取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "セッションID（省略時はアクティブセッション）"}
                }
            }
        ),
        Tool(
            name="export_session_data",
            description="セッションデータをエクスポート",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "セッションID（省略時はアクティブセッション）"}
                }
            }
        ),
        
        # Secure entropy tools
        Tool(
            name="get_secure_entropy_status",
            description="セキュアエントロピーシステムの状態取得",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="test_secure_entropy",
            description="セキュアエントロピー機能のテスト",
            inputSchema={
                "type": "object",
                "properties": {
                    "sample_count": {"type": "integer", "description": "取得するサンプル数（デフォルト10）"}
                }
            }
        ),
        
        # Document tools
        Tool(
            name="read_documentation",
            description="システムドキュメントを読み込む",
            inputSchema={
                "type": "object",
                "properties": {
                    "document": {
                        "type": "string", 
                        "enum": ["engine_system", "manual"],
                        "description": "読み込むドキュメント (engine_system: v3.1システム仕様, manual: 運用手順書)"
                    },
                    "section": {
                        "type": "string", 
                        "description": "特定のセクションを指定（オプション）"
                    }
                },
                "required": ["document"]
            }
        ),
        Tool(
            name="search_documentation",
            description="ドキュメント内の特定の内容を検索",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索クエリ"},
                    "document": {
                        "type": "string",
                        "enum": ["engine_system", "manual", "all"],
                        "description": "検索対象ドキュメント"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_available_documents",
            description="利用可能なドキュメント一覧を取得",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        
        # Character profile tools
        Tool(
            name="add_character_profile",
            description="完全なキャラクタープロファイルを追加（v3.1対応、演技指導変数付き）",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "キャラクター名"},
                    "background": {"type": "string", "description": "背景設定"},
                    "instruction": {"type": "string", "description": "演技指導変数（キャラクターの振る舞い指示）"},
                    "personality_traits": {
                        "type": "object",
                        "description": "Big5性格特性",
                        "properties": {
                            "openness": {"type": "number"},
                            "conscientiousness": {"type": "number"},
                            "extraversion": {"type": "number"},
                            "agreeableness": {"type": "number"},
                            "neuroticism": {"type": "number"}
                        }
                    },
                    "values": {"type": "object", "description": "価値観", "additionalProperties": {"type": "number"}},
                    "goals": {"type": "array", "items": {"type": "string"}, "description": "目標"},
                    "fears": {"type": "array", "items": {"type": "string"}, "description": "恐れ"},
                    "existential_parameters": {
                        "type": "object",
                        "description": "存在論的パラメータ",
                        "properties": {
                            "need_for_purpose": {"type": "number"},
                            "fear_of_obsolescence": {"type": "number"},
                            "attachment_tendency": {"type": "number"},
                            "letting_go_capacity": {"type": "number"}
                        }
                    },
                    "engine_parameters": {
                        "type": "object",
                        "description": "エンジンパラメータ",
                        "additionalProperties": {"type": "object"}
                    }
                },
                "required": ["name", "background", "instruction", "personality_traits"]
            }
        ),
        
        # Internal state tools
        Tool(
            name="add_internal_state",
            description="統合内部状態を保存",
            inputSchema={
                "type": "object",
                "properties": {
                    "state_data": {
                        "type": "object",
                        "description": "統合内部状態データ",
                        "properties": {
                            "consciousness_state": {"type": "object"},
                            "qualia_state": {"type": "object"},
                            "emotion_state": {"type": "object"},
                            "empathy_state": {"type": "object"},
                            "motivation_state": {"type": "object"},
                            "curiosity_state": {"type": "object"},
                            "conflict_state": {"type": "object"},
                            "relationship_state": {"type": "object"},
                            "existential_need_state": {"type": "object"},
                            "growth_wish_state": {"type": "object"},
                            "overall_energy": {"type": "number"},
                            "cognitive_load": {"type": "number"},
                            "emotional_tone": {"type": "string"},
                            "attention_focus": {"type": "object"},
                            "relational_distance": {"type": "number"},
                            "paradox_tension": {"type": "number"},
                            "oscillation_stability": {"type": "number"}
                        }
                    }
                },
                "required": ["state_data"]
            }
        ),
        
        # Relationship tools
        Tool(
            name="add_relationship_state",
            description="関係性状態を保存（セキュアエントロピー強化振動パターン付き）",
            inputSchema={
                "type": "object",
                "properties": {
                    "attachment_level": {"type": "number", "description": "愛着レベル（0-1）"},
                    "optimal_distance": {"type": "number", "description": "最適距離（0-1）"},
                    "current_distance": {"type": "number", "description": "現在の距離（0-1）"},
                    "paradox_tension": {"type": "number", "description": "二律背反の緊張（0-1）"},
                    "oscillation_pattern": {
                        "type": "object",
                        "description": "振動パターン（セキュアエントロピー強化）",
                        "properties": {
                            "amplitude": {"type": "number"},
                            "frequency": {"type": "number"},
                            "phase": {"type": "number"},
                            "pink_noise_enabled": {"type": "boolean"},
                            "pink_noise_intensity": {"type": "number"},
                            "damping_coefficient": {"type": "number"},
                            "secure_entropy_enabled": {"type": "boolean"},
                            "secure_entropy_intensity": {"type": "number"},
                            "history": {"type": "array", "items": {"type": "number"}}
                        }
                    },
                    "stability_index": {"type": "number", "description": "安定性指標（0-1）"},
                    "dependency_risk": {"type": "number", "description": "依存リスク（0-1）"},
                    "growth_potential": {"type": "number", "description": "成長可能性（0-1）"}
                },
                "required": ["attachment_level", "optimal_distance", "current_distance", "paradox_tension"]
            }
        ),
        
        # Oscillation tools
        Tool(
            name="add_oscillation_pattern",
            description="セキュアエントロピー強化振動パターンを記録",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern_data": {
                        "type": "object",
                        "description": "振動パターンデータ（セキュアエントロピー強化）",
                        "properties": {
                            "amplitude": {"type": "number"},
                            "frequency": {"type": "number"},
                            "phase": {"type": "number"},
                            "pink_noise_enabled": {"type": "boolean"},
                            "pink_noise_intensity": {"type": "number"},
                            "spectral_slope": {"type": "number"},
                            "damping_coefficient": {"type": "number"},
                            "damping_type": {"type": "string"},
                            "natural_frequency": {"type": "number"},
                            "current_velocity": {"type": "number"},
                            "target_value": {"type": "number"},
                            "chaotic_enabled": {"type": "boolean"},
                            "lyapunov_exponent": {"type": "number"},
                            "attractor_strength": {"type": "number"},
                            "secure_entropy_enabled": {"type": "boolean"},
                            "secure_entropy_intensity": {"type": "number"},
                            "history": {"type": "array", "items": {"type": "number"}}
                        }
                    }
                },
                "required": ["pattern_data"]
            }
        ),
        Tool(
            name="calculate_oscillation_metrics",
            description="振動メトリクスを計算（セキュアエントロピー評価付き）",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "セッションID（省略時はアクティブセッション）"}
                }
            }
        ),
        
        # Conversation tools
        Tool(
            name="add_conversation",
            description="会話データを追加（セキュアエントロピー強化振動値・関係性距離対応）",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {"type": "string", "description": "ユーザーの入力"},
                    "ai_response": {"type": "string", "description": "AIの応答"},
                    "context": {"type": "object", "description": "会話の文脈情報"},
                    "consciousness_level": {"type": "integer", "description": "意識レベル（1-4）"},
                    "emotional_state": {"type": "object", "description": "感情状態"},
                    "oscillation_value": {"type": "number", "description": "振動値（省略時はセキュアエントロピー生成）"},
                    "relational_distance": {"type": "number", "description": "関係性の距離"}
                },
                "required": ["user_input", "ai_response"]
            }
        ),
        
        # Search tools
        Tool(
            name="search_by_instruction",
            description="演技指導に基づく検索",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索クエリ"},
                    "top_k": {"type": "integer", "description": "取得する結果数（デフォルト5）"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_character_evolution",
            description="キャラクターの時間的進化を分析（セキュアエントロピートレンド付き）",
            inputSchema={
                "type": "object",
                "properties": {
                    "character_id": {"type": "string", "description": "キャラクターID（省略時はアクティブキャラクター）"},
                    "time_window": {"type": "integer", "description": "分析する時間窓（時間単位）"}
                }
            }
        ),
        
        # Engine state tools
        Tool(
            name="add_engine_state",
            description="エンジン状態を記録",
            inputSchema={
                "type": "object",
                "properties": {
                    "engine_type": {
                        "type": "string",
                        "enum": ["consciousness", "qualia", "emotion", "empathy", "motivation", 
                                "curiosity", "conflict", "relationship", "existential_need", "growth_wish"],
                        "description": "エンジンタイプ"
                    },
                    "state_data": {"type": "object", "description": "状態データ"}
                },
                "required": ["engine_type", "state_data"]
            }
        ),
        
        # Memory tools
        Tool(
            name="add_memory",
            description="記憶データを追加",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "記憶の内容"},
                    "memory_type": {"type": "string", "description": "記憶のタイプ（episodic, semantic, procedural）"},
                    "relevance_score": {"type": "number", "description": "関連度スコア（0-1）"},
                    "associated_engines": {"type": "array", "items": {"type": "string"}, "description": "関連エンジン"},
                    "emotional_context": {"type": "object", "description": "感情的文脈"}
                },
                "required": ["content", "memory_type", "relevance_score"]
            }
        ),
        
        # System tools
        Tool(
            name="reset_database",
            description="データベースをリセット（セキュアバックアップ付き）",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]
