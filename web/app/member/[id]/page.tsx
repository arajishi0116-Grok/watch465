import fs from "fs";
import path from "path";
import Link from "next/link";
import { notFound } from "next/navigation";

type Member = {
  id: string;
  name: string;
  name_kana: string;
  party: string;
  constituency: string;
  constituency_type: string;
  term_count: number;
  current_term_start: string;
  committees: string[];
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

type BillDetail = {
  session: number;
  name: string;
  status: string;
  url: string;
  is_primary: boolean;
  faction: string;
};

type KakuhoBill = {
  session: number;
  name: string;
  status: string;
  url: string;
  committee: string;
};

function StatCard({
  label,
  value,
  unit = "",
  highlight = false,
}: {
  label: string;
  value: number | string;
  unit?: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "bg-[#1a3a5c] text-white border-[#1a3a5c]" : "bg-white border-gray-200"}`}>
      <div className={`text-xs mb-1 ${highlight ? "text-blue-200" : "text-gray-500"}`}>{label}</div>
      <div className={`text-3xl font-bold ${highlight ? "text-white" : "text-gray-900"}`}>
        {value}
        {unit && <span className={`text-sm font-normal ml-1 ${highlight ? "text-blue-200" : "text-gray-500"}`}>{unit}</span>}
      </div>
    </div>
  );
}

const PARTY_COLORS: Record<string, string> = {
  自民: "bg-red-100 text-red-800",
  中道: "bg-blue-100 text-blue-800",
  維新: "bg-yellow-100 text-yellow-800",
  国民: "bg-green-100 text-green-800",
  参政: "bg-orange-100 text-orange-800",
  みらい: "bg-teal-100 text-teal-800",
};

export default function MemberPage({ params }: { params: { id: string } }) {
  const dataDir = path.join(process.cwd(), "..", "data");
  const membersPath = path.join(dataDir, "members.json");

  if (!fs.existsSync(membersPath)) notFound();

  const members: Member[] = JSON.parse(fs.readFileSync(membersPath, "utf-8"));

  // URL encoding されたIDにも対応
  const rawId = decodeURIComponent(params.id);
  const member = members.find((m) => m.id === rawId || m.id === params.id);
  if (!member) notFound();

  const statsPath = path.join(dataDir, "stats", `${member.id}.json`);
  const stats: Stats | null = fs.existsSync(statsPath)
    ? JSON.parse(fs.readFileSync(statsPath, "utf-8"))
    : null;

  const kokkaiBrowseUrl = `https://kokkai.ndl.go.jp/#/detail?speaker=${encodeURIComponent(member.name.replace(/　/g, ""))}&sessionFrom=1`;

  const billsIndexPath = path.join(dataDir, "bills_index.json");
  const billsIndex: Record<string, BillDetail[]> = fs.existsSync(billsIndexPath)
    ? JSON.parse(fs.readFileSync(billsIndexPath, "utf-8"))
    : {};
  const memberBills: BillDetail[] = billsIndex[member.id] ?? [];

  // 閣法：議員の所属委員会で審議した閣法を抽出
  const kakuhoIndexPath = path.join(dataDir, "kakuho_index.json");
  const kakuhoIndex: Record<string, KakuhoBill[]> = fs.existsSync(kakuhoIndexPath)
    ? JSON.parse(fs.readFileSync(kakuhoIndexPath, "utf-8"))
    : {};
  const memberCommittees = member.committees ?? [];
  const relatedKakuho: KakuhoBill[] = Object.values(kakuhoIndex)
    .flat()
    .filter((b) => memberCommittees.some((c) => b.committee.includes(c) || c.includes(b.committee)))
    .sort((a, b) => b.session - a.session);

  const partyColor = PARTY_COLORS[member.party] ?? "bg-gray-100 text-gray-700";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-[#1a3a5c] text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Link href="/" className="text-blue-300 hover:text-white text-sm transition-colors">
            ← Watch465 に戻る
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* 基本情報カード */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${partyColor}`}>
                  {member.party}
                </span>
                <span className="text-sm text-gray-500">{member.constituency}</span>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mt-2">
                {member.name.replace(/　/g, " ")}
              </h1>
              <div className="text-sm text-gray-400 mt-1">{member.name_kana}</div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-[#1a3a5c]">{member.term_count}<span className="text-base font-normal text-gray-500 ml-1">期</span></div>
              <div className="text-xs text-gray-400">当選回数</div>
              {member.current_term_start && (
                <div className="text-xs text-gray-400 mt-1">現任期：{member.current_term_start}〜</div>
              )}
            </div>
          </div>
          {member.committees.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-600">
              <span className="font-medium text-gray-700">所属委員会：</span>
              {member.committees.join("・")}
            </div>
          )}
        </div>

        {stats ? (
          <>
            {/* 活動状況 */}
            <h2 className="text-base font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-[#1a3a5c] rounded-full inline-block"></span>
              活動状況（令和8年2月18日〜）
            </h2>
            <div className="grid grid-cols-3 gap-3 mb-6">
              <StatCard label="実質発言数" value={stats.speech_count} unit="回" highlight />
              <StatCard label="委員会発言数" value={stats.committee_speech_count} unit="回" />
              <StatCard label="本会議発言数" value={stats.plenary_speech_count} unit="回" />
            </div>
            <div className="grid grid-cols-1 gap-3 mb-6">
              <StatCard label="質問主意書" value={stats.interpellations} unit="本" />
            </div>

            {/* 立法成果 */}
            <h2 className="text-base font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-[#1a3a5c] rounded-full inline-block"></span>
              立法成果
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <StatCard label="主提案" value={stats.bills_sponsored} unit="件" />
              <StatCard label="うち成立" value={stats.bills_sponsored_passed} unit="件" highlight={stats.bills_sponsored_passed > 0} />
              <StatCard label="うち審議中" value={stats.bills_sponsored_pending} unit="件" />
              <StatCard label="共同提案" value={stats.bills_cosponsored} unit="件" />
            </div>

            <div className="text-xs text-gray-400 mb-6">
              最終更新：{new Date(stats.updated_at).toLocaleDateString("ja-JP")}
            </div>
          </>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800 mb-6">
            この議員の統計データはまだ収集中です。
          </div>
        )}

        {/* 発議法案一覧 */}
        {memberBills.length > 0 && (
          <div className="mb-6">
            <h2 className="text-base font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-[#1a3a5c] rounded-full inline-block"></span>
              発議法案（直近4会期）
            </h2>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">会期</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500">法案名</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">状況</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {memberBills.map((bill, i) => (
                    <tr key={i} className="hover:bg-blue-50 transition-colors">
                      <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap text-sm">
                        第{bill.session}回
                      </td>
                      <td className="px-4 py-2.5">
                        <a
                          href={bill.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#1a3a5c] hover:underline font-medium"
                        >
                          {bill.name}
                        </a>
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          bill.status === "成立"
                            ? "bg-green-100 text-green-800"
                            : bill.status.includes("審議") || bill.status.includes("閉会")
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-600"
                        }`}>
                          {bill.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-1 text-xs text-gray-400">※ 主提案のみ表示</div>
          </div>
        )}

        {/* 閣法（関連委員会で審議） */}
        {relatedKakuho.length > 0 && (
          <div className="mb-6">
            <h2 className="text-base font-bold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-1 h-5 bg-[#1a3a5c] rounded-full inline-block"></span>
              所属委員会で審議した閣法（直近4会期）
            </h2>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">会期</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500">法案名</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 whitespace-nowrap">状況</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {relatedKakuho.map((bill, i) => (
                    <tr key={i} className="hover:bg-blue-50 transition-colors">
                      <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap text-sm">
                        第{bill.session}回
                      </td>
                      <td className="px-4 py-2.5">
                        {bill.url ? (
                          <a
                            href={bill.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[#1a3a5c] hover:underline font-medium"
                          >
                            {bill.name}
                          </a>
                        ) : (
                          <span className="font-medium text-gray-800">{bill.name}</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 whitespace-nowrap">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          bill.status === "成立"
                            ? "bg-green-100 text-green-800"
                            : bill.status.includes("審議") || bill.status.includes("閉会")
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-600"
                        }`}>
                          {bill.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-1 text-xs text-gray-400">※ 内閣提出法案。所属委員会で審議されたものを表示</div>
          </div>
        )}

        {/* 出典リンク */}
        <div className="pt-6 border-t border-gray-200">
          <a
            href={kokkaiBrowseUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-[#1a3a5c] hover:underline font-medium"
          >
            国会会議録検索システムで発言記録を検索 →
          </a>
          <div className="mt-2 text-xs text-gray-400">
            データ出典：国会会議録検索システム（国立国会図書館）・衆議院公式サイト
          </div>
        </div>
      </main>
    </div>
  );
}
