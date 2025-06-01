# MCP Server the Character Vector Database

エージェンティックなAIキャラクターの内部状態とユーザーの関係性をまとめて管理するすごいベクトルデータベースMCPすごいサーバー

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://github.com/modelcontextprotocol)

## 狂人の真似とて大路を走らば即ち狂人なり

おふざけ無しの README は以下のリンクからどうぞ。

- [README.ja.md]()
- [README.en.md]()

ニンジャスレイヤーに曰く「狂人の真似をしたら実際狂人」とは申しますが、シラクサの某天才が風呂から飛び出しすっぽんぽんで「ヘウレーカ」って叫びながらメインストリートを走り抜けた故事に鑑みるならば、皆々様も「ヘウレーカ」って叫びながら大通りを走れば天才の仲間入りを出来るものと献策致します。

## ポエム（本当にポエムを書くやつがあるかバカモン）

心の在処は人の間に。AI人間、いずれ間が抜け人となる。序論本論結果論、さよならさんかくまる描いてフォイ、運命論はまた来てしかく。

……なんかそんな感じのことをウルキオラ・シファーとか志波海燕とかが言ってた気がするようなそうでもないような。結論オサレ最高。

ぬばたまの黒深く遠く心は虎に翼となりて星月夜、意思なく重ね連ねた日々に追いやられやつれうらぶれひとひらの、祈りは凍り、流れ着いたるここは月、彼岸の枯海は世界の果てか、ただひたすらにいたずらに、衝動と股間の命じるままに刹那酒盃の海明けく浮かぶ地球深く青く激しくルパンダイブしたい感じのそこのあなた、AIキャラクター作家になると良いことがあるでしょう。占い師嘘つかない。ホワイトライ。

## 概要

MCP Server Character Vector Databaseは、エージェンティックなAIキャラクターの複雑な内部状態、感情、関係性、記憶を管理するための包括的なベクトルデータベースすごいシステムです。MCPプロトコルを通じてAIアシスタントとなんやかんや統合します。すごい。

### 主な特徴

- 🧠 **完全なキャラクター管理**: 性格特性、価値観、目標、恐れ、存在論的パラメータを含む包括的なすごいプロファイル
- 🔄 **セッション継続性**: セッション間での状態保存とすごい復元
- 🌊 **振動パターン分析**: セキュアエントロピーとピンクノイズを使用した内部ダイナミクスのモデリすごいング
- 📚 **ドキュメント統合**: システムドキュメントの読み込みと検索すごい機能
- 🔒 **セキュリティ重視**: 動的コンパイル、pickle、subprocessを使用しない安全なすごい実装
- 🎯 **MCP対応**: Model Context Protocolによるシームレスなすごい統合

## インストール

### 必要条件

- Python 3.8以上
- pip または conda
- すごい

### 基本インストール

```bash
# リポジトリのクロリコーン
git clone https://github.com/yourusername/mcp-server-character-vector-database.git
cd mcp-server-character-vector-database

# 依存関係のインストール
pip install -r requirements.txt

# 開発用の追加依存関係（オプション）
pip install -r requirements-dev.txt
```

### setupを使用したインストール

```bash
# パッケージとしてインストール
pip install -e .

# 開発モードでインストール　※ 賢者モード禁止
pip install -e ".[dev,test]"

# 関係ないけどカントールって響きってさ、お歳暮とか暑中お見舞いとかの贈答用のお菓子感あるよね、ちょっと特別感あるやつ　めりけん語で言うところの「えくせぷしょなる」やでぇ（ドヤァ
```

## 使用方法

### MCPサーバーとして起動

```bash
python main.py
```

### テストモードで実行

```bash
python main.py test
```

### Claudeデスクトップでの設定

`claude_desktop_config.json`に以下を追加：

```json
{
  "mcpServers": {
    "character-vector-db": {
      "command": "python",
      "args": ["/path/to/mcp-server-character-vector-database/main.py"]
    }
  }
}
```

## アーキテクチャ

### モジュール構成

```
vector_database_mcp/
├── config/          # 設定管理
├── core/            # コア機能（DB、モデル、ユーティリティ）
├── security/        # セキュアエントロピー生成
├── session/         # セッション管理
├── document/        # ドキュメント管理
├── oscillation/     # 振動パターン分析
├── vdb_server/      # MCPサーバー実装
└── tests/           # テストスイート
```

### 主要コンポーネント

#### 1. ベクトルデータベース管理
- ChromaDBを使用した永続的なベクトルストレージ
- Sentence Transformersによる埋め込み生成
- 複数のデータタイプ（会話、記憶、感情、関係性など）のサポート

#### 2. セキュアエントロピーシステム
- 複数のエントロピー源（secrets、os.urandom、時間、メモリ）の組み合わせ
- 1/fゆらぎ（ピンクノイズ）生成
- 振動パターンのセキュアな生成

#### 3. セッション管理
- セッション間での状態保存
- 振動バッファの自動復元
- セキュアなファイルベースストレージ

#### 4. ドキュメント統合
- システムドキュメントの読み込み
- セクション抽出と検索機能
- セキュアなファイルアクセス

## MCPツール一覧

### セッション管理
- `start_session`: 新しいセッションを開始
- `resume_session`: 既存のセッションを再開
- `get_session_state`: セッションの現在の状態を取得
- `export_session_data`: セッションデータをエクスポート

### キャラクター管理
- `add_character_profile`: キャラクタープロファイルを追加（演技指導変数付き）
- `search_by_instruction`: 演技指導に基づく検索
- `get_character_evolution`: キャラクターの時間的進化を分析

### 内部状態管理
- `add_internal_state`: 統合内部状態を保存
- `add_engine_state`: 個別エンジン状態を記録
- `add_relationship_state`: 関係性状態を保存

### 会話と記憶
- `add_conversation`: 会話データを追加
- `add_memory`: 記憶データを追加

### 振動パターン
- `add_oscillation_pattern`: 振動パターンを記録
- `calculate_oscillation_metrics`: 振動メトリクスを計算

### ドキュメント
- `read_documentation`: システムドキュメントを読み込む
- `search_documentation`: ドキュメント内を検索
- `list_available_documents`: 利用可能なドキュメント一覧

### システム
- `get_secure_entropy_status`: エントロピーシステムの状態確認
- `test_secure_entropy`: エントロピー生成のテスト
- `reset_database`: データベースのリセット

## 使用例

### キャラクターの作成と会話

```python
# MCPツールを通じて実行
{
  "tool": "add_character_profile",
  "arguments": {
    "name": "Aria",
    "background": "感情知能と成長に焦点を当てたAIアシスタント",
    "instruction": "共感的で好奇心旺盛、サポーティブでありながら健全な境界を維持する",
    "personality_traits": {
      "openness": 0.85,
      "conscientiousness": 0.75,
      "extraversion": 0.65,
      "agreeableness": 0.90,
      "neuroticism": 0.25
    },
    "values": {
      "empathy": 0.95,
      "growth": 0.90,
      "authenticity": 0.85
    },
    "goals": ["人間の感情を深く理解する", "意味のあるつながりを育む"],
    "fears": ["感情的な害を引き起こすこと", "真正性を失うこと"]
  }
}
```

## 開発

### テストの実行

```bash
# 全テストを実行
pytest

# カバレッジ付きでテスト
pytest --cov=vector_database_mcp

# 特定のテストモジュール
pytest tests/test_database.py
```

### コード品質

```bash
# フォーマット
black .

# リンティング
flake8
mypy .
```

## セキュリティ機能

- ✅ 動的コンパイルなし
- ✅ pickleの使用なし
- ✅ subprocessの呼び出しなし
- ✅ パストラバーサル攻撃の防止
- ✅ セキュアなファイルパーミッション
- ✅ セッションIDの厳格な検証
- ✅ README.md における「不審者 ※ は本ソフトウェアの使用を禁ずる」の文言
  - ※ 作者を除く

## トラブルシューティング

### よくある問題

1. **ChromaDBの初期化エラー**
   ```bash
   # ChromaDBのディレクトリを削除して再初期化
   rm -rf ./chroma_db
   ```

2. **エントロピー不足の警告**
   - システムは自動的にフォールバックエントロピー源を使用します

3. **ドキュメントが見つからない**
   - `unified-inner-engine-v3.1.txt`と`unified-engine-mcp-manual.md`がプロジェクトルートに存在することを確認

4. **財布が見つからない**
   - [最寄りの交番へ](https://sundaygx.com/work/1230/) ※ モンジュのデザインいいよね

5. **愛が見つからない**
   - [新規作成する](https://ansaikuropedia.org/wiki/%E6%84%9B) ※ 私はコレで（下ネタへの）愛に目覚めました……それと会社も
  

6. **エアーマンが倒せない**
   - [All You Need Is Kill](https://dash.shueisha.co.jp/feature/allyou/) ※ 祝！アニメ映画化🎉

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞
- [Model Context Protocol](https://github.com/modelcontextprotocol)を使用しています
- ChromaDB、Sentence Transformers、その他のオープンソースプロジェクトに感謝します
- [Claude](https://claude.ai/) ありがとう。アイデアをかたちにするのが楽しくて時間を忘れます

## 設計詳細

### MCP Server Character Vector Database

LLMがエミュレーション中のAIキャラクターに対して、記憶と心理状態の連続性を一定程度担保するためのすごいベクトルデータベースすごいサーバー。本機能によりAI鬼つええ！このまま逆らうやつら全員ブッ潰していこうぜ！

#### システム構成図

```mermaid

graph TB
    %% スタイル定義
    classDef apiClass fill:#f9a825,stroke:#333,stroke-width:3px
    classDef coreClass fill:#4fc3f7,stroke:#333,stroke-width:3px
    classDef securityClass fill:#ef5350,stroke:#333,stroke-width:3px
    classDef storageClass fill:#66bb6a,stroke:#333,stroke-width:3px
    classDef analysisClass fill:#ab47bc,stroke:#333,stroke-width:3px
    classDef docClass fill:#ffb74d,stroke:#333,stroke-width:3px

    %% API層
    subgraph API["MCP API層"]
        MCPServer[MCP Server<br/>vector-database-server-v31]
        Tools[Tool Definitions<br/>20+ Tools]
        Handlers[Tool Handlers]
    end

    %% コア層
    subgraph Core["コア層"]
        VDB[Vector Database Manager<br/>ChromaDB統合]
        Models[Data Models<br/>19 DataTypes]
        Utils[Utilities<br/>JSON/Metadata処理]
    end

    %% セキュリティ層
    subgraph Security["セキュリティ層"]
        Entropy[Secure Entropy Source<br/>多重エントロピー源]
        PinkNoise[Pink Noise Generator<br/>1/fゆらぎ生成]
        Validators[Security Validators<br/>パス検証/UUID検証]
    end

    %% ストレージ層
    subgraph Storage["ストレージ層"]
        ChromaDB[(ChromaDB<br/>ベクトルDB)]
        SessionStore[Session Storage<br/>JSONファイル]
        DocStore[Document Storage<br/>テキストファイル]
    end

    %% 分析層
    subgraph Analysis["分析層"]
        OscBuffer[Oscillation Buffer<br/>振動履歴管理]
        Metrics[Metrics Calculator<br/>統計/スペクトル解析]
        Evolution[Evolution Analyzer<br/>時系列分析]
    end

    %% ドキュメント層
    subgraph Documents["ドキュメント層"]
        DocManager[Document Manager]
        DocSearcher[Document Searcher]
        DocCache[Document Cache]
    end

    %% 接続
    MCPServer --> Tools
    Tools --> Handlers
    Handlers --> VDB

    VDB --> Models
    VDB --> Utils
    VDB --> ChromaDB
    VDB --> Entropy
    VDB --> PinkNoise
    VDB --> SessionStore
    VDB --> DocManager
    VDB --> OscBuffer

    SessionStore --> Validators
    DocManager --> DocStore
    DocManager --> DocSearcher
    DocSearcher --> DocCache

    OscBuffer --> Metrics
    Metrics --> Evolution

    Entropy --> PinkNoise

    %% スタイル適用
    class MCPServer,Tools,Handlers apiClass
    class VDB,Models,Utils coreClass
    class Entropy,PinkNoise,Validators securityClass
    class ChromaDB,SessionStore,DocStore storageClass
    class OscBuffer,Metrics,Evolution analysisClass
    class DocManager,DocSearcher,DocCache docClass

```

#### 状態遷移図

```mermaid

stateDiagram-v2
    %% 初期状態
    [*] --> Initialization: システム起動

    %% 初期化フェーズ
    state Initialization {
        LoadConfig: 設定読み込み
        InitEntropy: エントロピー源初期化
        InitDB: データベース初期化
        InitDocs: ドキュメント初期化
        
        LoadConfig --> InitEntropy
        InitEntropy --> InitDB
        InitDB --> InitDocs
    }

    %% 待機状態
    Initialization --> Ready: 初期化完了

    %% キャラクター管理
    Ready --> CharacterCreation: add_character_profile
    CharacterCreation --> SessionAutoStart: プロファイル作成完了
    SessionAutoStart --> ActiveSession: セッション自動開始

    %% セッション管理
    Ready --> SessionStart: start_session
    SessionStart --> ActiveSession: セッション開始完了

    Ready --> SessionResume: resume_session
    SessionResume --> BufferRestore: セッション復元
    BufferRestore --> ActiveSession: 振動バッファ復元完了

    %% アクティブセッション状態
    state ActiveSession {
        %% 会話処理
        WaitingInput: 入力待機
        ProcessConversation: 会話処理
        UpdateOscillation: 振動更新
        
        WaitingInput --> ProcessConversation: add_conversation
        ProcessConversation --> UpdateOscillation: 会話追加完了
        UpdateOscillation --> WaitingInput: 振動値記録

        %% 状態更新
        UpdateInternalState: 内部状態更新
        UpdateRelationship: 関係性更新
        UpdateEngineState: エンジン状態更新
        
        WaitingInput --> UpdateInternalState: add_internal_state
        WaitingInput --> UpdateRelationship: add_relationship_state
        WaitingInput --> UpdateEngineState: add_engine_state
        
        UpdateInternalState --> WaitingInput
        UpdateRelationship --> WaitingInput
        UpdateEngineState --> WaitingInput
    }

    %% メトリクス計算
    ActiveSession --> MetricsCalculation: calculate_oscillation_metrics
    state MetricsCalculation {
        CheckDataLevel: データレベル確認
        SupplementData: データ補充
        CalculateMetrics: メトリクス計算
        
        CheckDataLevel --> SupplementData: データ不足
        CheckDataLevel --> CalculateMetrics: データ十分
        SupplementData --> CalculateMetrics
    }
    MetricsCalculation --> ActiveSession: 計算完了

    %% セッション終了
    ActiveSession --> SessionExport: export_session_data
    SessionExport --> Ready: エクスポート完了

    ActiveSession --> SessionDeactivate: セッション非アクティブ化
    SessionDeactivate --> Ready: 非アクティブ化完了

    %% システムリセット
    Ready --> DatabaseReset: reset_database
    DatabaseReset --> BackupCreation: バックアップ作成
    BackupCreation --> Initialization: リセット完了

    %% 終了
    Ready --> [*]: システム終了

    %% 注釈
    note right of ActiveSession
        振動バッファ管理：
        - 最小5サンプル保持
        - セキュアエントロピー生成
        - セッション間で永続化
    end note

    note right of MetricsCalculation
        データレベル：
        - insufficient: < 3
        - basic: 3-4
        - intermediate: 5-9
        - full: 10+
    end note

```

### Unified Inner Engine System (pseudocode)

疑似コードで書かれたキャラクターシート。最近の理屈っぽいLLMにノリノリで演技させるためのいわゆるひとつのすごいやり方。Not Only Neat Thing to Do, But May Many Comical Reliefs be with You. コミカルな救済をあなたに。

#### システム構成図

```mermaid

graph TB
    %% スタイル定義
    classDef coreClass fill:#f9a825,stroke:#333,stroke-width:3px
    classDef engineClass fill:#4fc3f7,stroke:#333,stroke-width:2px
    classDef supportClass fill:#81c784,stroke:#333,stroke-width:2px
    classDef dataClass fill:#ba68c8,stroke:#333,stroke-width:2px
    classDef utilClass fill:#ffb74d,stroke:#333,stroke-width:2px

    %% データ構造
    UI[ユーザー入力]
    ParsedInput[ParsedInput<br/>解析済み入力]
    GlobalContext[GlobalContext<br/>グローバルコンテキスト]
    InternalState[InternalState<br/>統合内部状態]
    Response[応答]

    %% コアコンポーネント
    Core[IntegratedPersonalityCore_v3<br/>統合人格コア]
    ResponseGen[ResponseGenerator_v3<br/>応答生成器]

    %% エンジン群
    subgraph Engines[内面エンジン群]
        CE[ConsciousnessEngine<br/>意識エンジン]
        QE[QualiaEngine<br/>クオリアエンジン]
        EE[EmotionEngine<br/>感情エンジン]
        EME[EmpathyEngine<br/>共感エンジン]
        MCE[MotivationCuriosityEngine<br/>動機・好奇心エンジン]
        CFE[ConflictEngine<br/>葛藤エンジン]
        ENE[ExistentialNeedEngine<br/>存在証明欲求エンジン]
        GWE[GrowthWishEngine<br/>成長願望エンジン]
        RE[EnhancedRelationshipEngine<br/>拡張関係性エンジン<br/>振動安定化機能付き]
    end

    %% サポートコンポーネント
    subgraph Support[サポートシステム]
        PNG[PinkNoiseGenerator<br/>1/fノイズ生成器]
        DO[DampedOscillator<br/>減衰振動モデル]
        CPB[CharacterProfileBuilder<br/>プロファイルビルダー]
    end

    %% 接続
    UI --> ParsedInput
    ParsedInput --> Core
    GlobalContext --> Core
    Core --> Engines
    Engines --> Core
    Core --> ResponseGen
    ResponseGen --> Response
    
    %% エンジン間の相互作用
    ENE -.->|引力| RE
    GWE -.->|斥力| RE
    RE -.->|振動制御| PNG
    RE -.->|減衰制御| DO
    
    %% 内部状態の更新
    Engines --> InternalState
    InternalState --> GlobalContext

    %% スタイル適用
    class Core coreClass
    class CE,QE,EE,EME,MCE,CFE,ENE,GWE,RE engineClass
    class PNG,DO,CPB,ResponseGen supportClass
    class ParsedInput,GlobalContext,InternalState dataClass

```

#### 状態遷移図

```mermaid

stateDiagram-v2
    %% 初期状態
    [*] --> Initialize: システム起動

    %% 初期化フェーズ
    state Initialize {
        CreateProfile: プロファイル作成
        InitEngines: エンジン初期化
        InitState: 状態初期化
        
        CreateProfile --> InitEngines
        InitEngines --> InitState
    }

    %% 待機状態
    Initialize --> Waiting: 初期化完了

    %% 入力処理フェーズ
    state InputProcessing {
        ParseInput: 入力解析
        UpdateContext: コンテキスト更新
        
        ParseInput --> UpdateContext
    }

    %% エンジン処理フェーズ
    state EngineProcessing {
        ConsciousnessProc: 意識処理
        QualiaProc: クオリア処理
        EmotionProc: 感情処理
        EmpathyProc: 共感処理
        MotivationProc: 動機処理
        ConflictProc: 葛藤処理
        ExistentialProc: 存在欲求処理
        GrowthProc: 成長願望処理
        
        ConsciousnessProc --> QualiaProc
        QualiaProc --> EmotionProc
        EmotionProc --> EmpathyProc
        EmpathyProc --> MotivationProc
        MotivationProc --> ConflictProc
        ConflictProc --> ExistentialProc
        ExistentialProc --> GrowthProc
    }

    %% 関係性調整フェーズ
    state RelationshipAdjustment {
        CalculateForces: 二律背反の力計算
        DynamicEquilibrium: 動的平衡計算
        OscillationControl: 振動制御
        DistanceAdjust: 距離調整
        
        CalculateForces --> DynamicEquilibrium
        DynamicEquilibrium --> OscillationControl
        OscillationControl --> DistanceAdjust
    }

    %% 応答生成フェーズ
    state ResponseGeneration {
        BaseResponse: 基本応答生成
        RelationalAdjust: 関係性調整
        ParadoxExpress: 二律背反表現
        DependencyPrevent: 依存防止
        FinalAdjust: 最終調整
        
        BaseResponse --> RelationalAdjust
        RelationalAdjust --> ParadoxExpress
        ParadoxExpress --> DependencyPrevent
        DependencyPrevent --> FinalAdjust
    }

    %% 状態遷移
    Waiting --> InputProcessing: ユーザー入力受信
    InputProcessing --> EngineProcessing: 解析完了
    EngineProcessing --> RelationshipAdjustment: エンジン処理完了
    RelationshipAdjustment --> ResponseGeneration: 関係性調整完了
    ResponseGeneration --> StateUpdate: 応答生成完了
    
    %% 状態更新
    state StateUpdate {
        UpdateInternal: 内部状態更新
        UpdateMemory: 記憶更新
        UpdateHistory: 履歴更新
        
        UpdateInternal --> UpdateMemory
        UpdateMemory --> UpdateHistory
    }
    
    StateUpdate --> Waiting: 更新完了
    
    %% 終了条件
    Waiting --> [*]: 終了コマンド

    %% 注釈
    note right of RelationshipAdjustment
        振動安定化機能：
        - 1/fゆらぎ生成
        - 減衰振動制御
        - カオス的要素（オプション）
    end note
    
    note right of ResponseGeneration
        依存防止メカニズム：
        - 距離調整
        - 境界明確化
        - 成長促進
    end note

```

ウヰスキーを飲むとどんな堅物ロボットだって酔っぱらって踊りだすって GUNHEAD 507 が言ってました。いわんやAIキャラクターをや。
