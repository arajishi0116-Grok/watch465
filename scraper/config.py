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
STATS_DIR = "../data/stats"
RANKINGS_DIR = "../data/rankings"
