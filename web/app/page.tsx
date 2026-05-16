import fs from "fs";
import path from "path";
import Link from "next/link";

type Member = {
  id: string;
  name: string;
  name_kana: string;
  party: string;
  constituency: string;
  term_count: number;
};

type Stats = {
  speech_count: number;
  committee_speech_count: number;
  plenary_speech_count: number;
  interpellations: number;
  bills_sponsored: number;
  bills_sponsored_passed: number;
  bills_sponsored_pending: number;
  bills_cosponsored: number;
  updated_at: string;
};

type MemberWithStats = Member & Partial<Stats>;

const PARTY_TABS = ["全員", "自民", "中道", "維新", "国民", "参政", "みらい", "無所属等"];

const PARTY_COLORS: Record<string, string> = {
  自民: "bg-red-100 text-red-800 border border-red-200",
  中道: "bg-blue-100 text-blue-800 border border-blue-200",
  維新: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  国民: "bg-green-100 text-green-800 border border-green-200",
  参政: "bg-orange-100 text-orange-800 border border-orange-200",
  みらい: "bg-teal-100 text-teal-800 border border-teal-200",
};

function getPartyBadgeClass(party: string) {
  return PARTY_COLORS[party] ?? "bg-gray-100 text-gray-600 border border-gray-200";
}

function loadData(): MemberWithStats[] {
  const dataDir = path.join(process.cwd(), "..", "data");
  const membersPath = path.join(dataDir, "members.json");
  if (!fs.existsSync(membersPath)) return [];
  const members: Member[] = JSON.parse(fs.readFileSync(membersPath, "utf-8"));
  return members.map((m) => {
    const statsPath = path.join(dataDir, "stats", `${m.id}.json`);
    if (!m.id || !fs.existsSync(statsPath)) return m;
    const stats: Stats = JSON.parse(fs.readFileSync(statsPath, "utf-8"));
    return { ...m, ...stats };
  });
}


export default function Home({
  searchParams,
}: {
  searchParams: { tab?: string; sort?: string; dir?: string };
}) {
  const members = loadData();
  const activeTab = searchParams.tab ?? "全員";
  const sortKey = (searchParams.sort ?? "speech_count") as keyof MemberWithStats;
  const sortDir = searchParams.dir ?? "desc";

  const filtered =
    activeTab === "全員"
      ? members
      : members.filter((m) =>
          activeTab === "無所属等"
            ? !PARTY_TABS.slice(1, -1).some((p) => m.party.startsWith(p))
            : m.party.startsWith(activeTab)
        );

  const sorted = [...filtered].sort((a, b) => {
    const av = (a[sortKey] as number) ?? -1;
    const bv = (b[sortKey] as number) ?? -1;
    return sortDir === "asc" ? av - bv : bv - av;
  });

  const withStats = sorted.filter((m) => m.speech_count != null);
  const noStats = sorted.filter((m) => m.speech_count == null);
  const display = [...withStats, ...noStats];

  // 列ヘッダーのリンクURL生成（同じ列を再クリックで昇降順切り替え）
  function sortUrl(key: string) {
    const newDir = sortKey === key && sortDir === "desc" ? "asc" : "desc";
    return `/?tab=${activeTab}&sort=${key}&dir=${newDir}`;
  }
  function sortIcon(key: string) {
    if (sortKey !== key) return " ↕";
    return sortDir === "desc" ? " ↓" : " ↑";
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-[#1a3a5c] text-white shadow-lg">
        <div className="max-w-screen-2xl mx-auto px-4 py-5">
          <div className="flex items-baseline gap-3">
            <h1 className="text-4xl font-bold tracking-tight">Watch465</h1>
            <span className="text-blue-300 text-lg font-light">衆議院議員 活動記録</span>
          </div>
          <p className="mt-3 text-blue-100 text-sm leading-relaxed max-w-3xl">
            このサイトは国会議員（衆議院）の活動状況を、国会の公式データを使用して見える化し、政治的偏見なしで有権者に提供することを目的としています。<br />
            Claude.AIを使用しています。内容に誤りがありましたら、お手数ですが公式Xよりご指摘ください。
          </p>
          <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-blue-300">
            <span>対象期間：2025年3月〜（第217回国会〜）</span>
            <span>毎週月曜日 自動更新</span>
            <span>データ出典：国会会議録検索システム・衆議院公式サイト</span>
          </div>
        </div>
      </header>

      <main className="max-w-screen-2xl mx-auto px-4 py-6">
        {/* 党派タブ */}
        <div className="flex flex-wrap gap-2 mb-5">
          {PARTY_TABS.map((tab) => (
            <Link
              key={tab}
              href={`/?tab=${tab}&sort=${sortKey}`}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                activeTab === tab
                  ? "bg-[#1a3a5c] text-white border-[#1a3a5c]"
                  : "bg-white text-gray-700 border-gray-300 hover:border-[#1a3a5c] hover:text-[#1a3a5c]"
              }`}
            >
              {tab}
              {tab !== "全員" && (
                <span className="ml-1 text-xs opacity-60">
                  {tab === "無所属等"
                    ? members.filter((m) => !PARTY_TABS.slice(1, -1).some((p) => m.party.startsWith(p))).length
                    : members.filter((m) => m.party.startsWith(tab)).length}
                </span>
              )}
            </Link>
          ))}
        </div>

        {/* ランキングテーブル */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 w-10">#</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 min-w-[9rem]">議員名</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500">党派</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">選挙区</th>
                {[
                  ["speech_count", "実質発言数"],
                  ["committee_speech_count", "委員会発言数"],
                  ["plenary_speech_count", "本会議発言数"],
                  ["interpellations", "質問主意書"],
                  ["bills_sponsored", "主提案"],
                  ["bills_cosponsored", "共同提案"],
                  ["bills_sponsored_pending", "審議中"],
                  ["bills_sponsored_passed", "成立"],
                ].map(([key, label]) => (
                  <th key={key} className="px-2 py-3 text-right text-xs font-semibold whitespace-nowrap">
                    <Link href={sortUrl(key)}
                      className={`hover:text-[#1a3a5c] ${sortKey === key ? "text-[#1a3a5c] underline" : "text-gray-500"}`}>
                      {label}{sortIcon(key)}
                    </Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {display.map((m, i) => (
                <tr key={m.id || m.name} className="hover:bg-blue-50 transition-colors">
                  <td className="px-3 py-2.5 text-sm text-gray-400 font-mono">{i + 1}</td>
                  <td className="px-3 py-2.5">
                    <Link
                      href={`/member/${encodeURIComponent(m.id || m.name)}`}
                      className="text-sm font-semibold text-[#1a3a5c] hover:underline whitespace-nowrap"
                    >
                      {m.name.replace(/　/g, " ")}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${getPartyBadgeClass(m.party)}`}>
                      {m.party}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-sm text-gray-600 whitespace-nowrap">{m.constituency}</td>
                  {([
                    ["speech_count", m.speech_count],
                    ["committee_speech_count", m.committee_speech_count],
                    ["plenary_speech_count", m.plenary_speech_count],
                    ["interpellations", m.interpellations],
                    ["bills_sponsored", m.bills_sponsored],
                    ["bills_cosponsored", m.bills_cosponsored],
                    ["bills_sponsored_pending", m.bills_sponsored_pending],
                    ["bills_sponsored_passed", m.bills_sponsored_passed],
                  ] as [string, number | undefined][]).map(([key, val]) => (
                    <td key={key} className="px-2 py-2.5 text-right">
                      <span className={`text-sm font-semibold font-mono ${val != null ? "text-gray-900" : "text-gray-300"}`}>
                        {val != null ? val : "—"}
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-xs text-gray-400">
          {display.length}人表示（うちデータあり {withStats.length}人）
        </div>
      </main>
    </div>
  );
}
