# WATCH465 設定ファイル
# 指標の定義・閾値はここで一元管理し、aboutページにも反映する

# 国会会議録API
KOKKAI_API_BASE = "https://kokkai.ndl.go.jp/api/speech"
REQUEST_INTERVAL_SEC = 3  # APIリクエスト間隔（秒）
MAX_RECORDS_PER_REQUEST = 100

# 実質発言判定：内容語（名詞＋動詞）数の閾値
SUBSTANTIVE_SPEECH_MIN_WORDS = 10

# 除外対象の役割（議長・大臣等）
EXCLUDED_SPEAKER_ROLES = ["議長", "委員長", "国務大臣", "副大臣", "大臣政務官"]

# データパス
DATA_DIR = "../data"
MEMBERS_JSON = "../data/members.json"
MEMBERS_SANGIIN_JSON = "../data/members_sangiin.json"   # 将来: 参議院
SPEECHES_DIR = "../data/speeches"
STATS_DIR = "../data/stats"
STATS_PREV_DIR = "../data/stats_prev"  # 前任期（第50回選挙後）
RANKINGS_DIR = "../data/rankings"

# 発言取得の起点（2000年以降のみ）
SPEECHES_FROM_DATE = "2000-01-01"

# 任期区切り
# 現任期: 第51回衆院選（2026-02-06）後 → 第221回特別会召集日から
CURRENT_TERM_START = "2026-02-18"
# 前任期: 第50回衆院選（2024-10-27）後 → 第215回特別会召集日〜解散日
PREV_TERM_START = "2024-11-11"
PREV_TERM_END   = "2026-01-23"

# 院の識別子
CHAMBER_SHUGIIN = "shugiin"
CHAMBER_SANGIIN = "sangiin"
