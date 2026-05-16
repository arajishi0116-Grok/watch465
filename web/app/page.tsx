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
  committee_attendance_rate: number;
  committee_speech_rate: number;
  plenary_attendance_rate: number;
  interpellations: number;
  bills_sponsored: number;
  bills_cosponsored: number;
  updated_at: string;
};

type MemberWithStats = Member & Partial<Stats>;

const PARTY_TABS = ["全員", "自民", "立憲", "維新", "公明", "国民", "参政", "れいわ", "その他"];

const PARTY_COLORS: Record<string, string> = {
  自民: "bg-red-100 text-red-800",
  立憲: "bg-blue-100 text-blue-800",
  維新: "bg-yellow-100 text-yellow-800",
  公明: "bg-purple-100 text-purple-800",
  国民: "bg-green-100 text-green-800",
  参政: "bg-orange-100 text-orange-800",
  れいわ: "bg-pink-100 text-pink-800",
};

function getPartyBadgeClass(party: string) {
  return PARTY_COLORS[party] ?? "bg-gray-100 text-gray-800";
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
  searchParams: { tab?: string; sort?: string };
}) {
  const members = loadData();
  const activeTab = searchParams.tab ?? "全員";
  const sortKey = (searchParams.sort ?? "committee_attendance_rate") as keyof MemberWithStats;

  const filtered =
    activeTab === "全員"
      ? members
      : members.filter((m) =>
          activeTab === "その他"
            ? !PARTY_TABS.slice(1, -1).some((p) => m.party.startsWith(p))
            : m.party.startsWith(activeTab)
        );

  const sorted = [...filtered].sort((a, b) => {
    const av = (a[sortKey] as number) ?? -1;
    const bv = (b[sortKey] as number) ?? -1;
    return bv - av;
  });

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">WATCH465</h1>
        <p className="mt-2 text-gray-600">
          衆議院議員465人の国会活動記録。公式データのみ使用。
        </p>
      </div>

      {/* 党派タブ */}
      <div className="flex flex-wrap gap-2 mb-6">
        {PARTY_TABS.map((tab) => (
          <Link
            key={tab}
            href={`/?tab=${tab}&sort=${sortKey}`}
            className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
              activeTab === tab
                ? "bg-gray-900 text-white border-gray-900"
                : "bg-white text-gray-700 border-gray-300 hover:border-gray-500"
            }`}
          >
            {tab}
          </Link>
        ))}
      </div>

      {/* ランキングテーブル */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3 text-left">#</th>
                <th className="px-4 py-3 text-left">氏名</th>
                <th className="px-4 py-3 text-left">党派</th>
                <th className="px-4 py-3 text-left">選挙区</th>
                <th className="px-4 py-3 text-right">
                  <Link href={`/?tab=${activeTab}&sort=committee_attendance_rate`} className="hover:text-blue-600">
                    委員会<br />発言率
                  </Link>
                </th>
                <th className="px-4 py-3 text-right">
                  <Link href={`/?tab=${activeTab}&sort=plenary_attendance_rate`} className="hover:text-blue-600">
                    本会議<br />発言率
                  </Link>
                </th>
                <th className="px-4 py-3 text-right">
                  <Link href={`/?tab=${activeTab}&sort=interpellations`} className="hover:text-blue-600">
                    質問<br />主意書
                  </Link>
                </th>
                <th className="px-4 py-3 text-right">
                  <Link href={`/?tab=${activeTab}&sort=bills_sponsored`} className="hover:text-blue-600">
                    主提案
                  </Link>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((m, i) => (
                <tr key={m.id || m.name} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400 w-12">{i + 1}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/member/${m.id || encodeURIComponent(m.name)}`}
                      className="font-medium text-blue-700 hover:underline"
                    >
                      {m.name.replace(/　/g, " ")}
                    </Link>
                    <div className="text-xs text-gray-400">{m.name_kana}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getPartyBadgeClass(m.party)}`}>
                      {m.party}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{m.constituency}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {m.committee_attendance_rate != null ? `${m.committee_attendance_rate}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {m.plenary_attendance_rate != null ? `${m.plenary_attendance_rate}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {m.interpellations != null ? m.interpellations : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {m.bills_sponsored != null ? m.bills_sponsored : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 text-xs text-gray-400">
        データ出典：国会会議録検索システム（国立国会図書館）・衆議院公式サイト
      </div>
    </main>
  );
}
