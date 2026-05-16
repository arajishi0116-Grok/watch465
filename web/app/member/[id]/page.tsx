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
  committee_attendance_rate: number;
  committee_speech_rate: number;
  plenary_attendance_rate: number;
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

function StatCard({
  label,
  value,
  unit = "",
}: {
  label: string;
  value: number | string;
  unit?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900">
        {value}
        {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
      </div>
    </div>
  );
}

export default function MemberPage({ params }: { params: { id: string } }) {
  const dataDir = path.join(process.cwd(), "..", "data");
  const membersPath = path.join(dataDir, "members.json");

  if (!fs.existsSync(membersPath)) notFound();

  const members: Member[] = JSON.parse(fs.readFileSync(membersPath, "utf-8"));
  const member = members.find((m) => m.id === params.id);
  if (!member) notFound();

  const statsPath = path.join(dataDir, "stats", `${member.id}.json`);
  const stats: Stats | null = fs.existsSync(statsPath)
    ? JSON.parse(fs.readFileSync(statsPath, "utf-8"))
    : null;

  const kokkaiBrowseUrl = `https://kokkai.ndl.go.jp/#/detail?speaker=${encodeURIComponent(member.name.replace(/　/g, ""))}&sessionFrom=1`;

  // 法案インデックスから該当議員の法案を取得
  const billsIndexPath = path.join(dataDir, "bills_index.json");
  const billsIndex: Record<string, BillDetail[]> = fs.existsSync(billsIndexPath)
    ? JSON.parse(fs.readFileSync(billsIndexPath, "utf-8"))
    : {};
  const memberBills: BillDetail[] = billsIndex[member.id] ?? [];

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <Link href="/" className="text-sm text-blue-600 hover:underline mb-6 inline-block">
        ← ランキングに戻る
      </Link>

      {/* 基本情報 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{member.name.replace(/　/g, " ")}</h1>
        <div className="text-sm text-gray-500 mt-1">{member.name_kana}</div>
        <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-700">
          <span>党派：<strong>{member.party}</strong></span>
          <span>選挙区：<strong>{member.constituency}</strong></span>
          <span>当選回数：<strong>{member.term_count}期</strong></span>
          {member.current_term_start && (
            <span>現任期開始：<strong>{member.current_term_start}</strong></span>
          )}
        </div>
        {member.committees.length > 0 && (
          <div className="mt-3 text-sm text-gray-600">
            委員会：{member.committees.join("・")}
          </div>
        )}
      </div>

      {stats ? (
        <>
          {/* 活動状況 */}
          <h2 className="text-lg font-semibold text-gray-800 mb-3">活動状況（直近1年）</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
            <StatCard label="委員会発言率" value={stats.committee_attendance_rate} unit="%" />
            <StatCard label="本会議発言率" value={stats.plenary_attendance_rate} unit="%" />
            <StatCard label="質問主意書" value={stats.interpellations} unit="本" />
          </div>

          {/* 立法成果 */}
          <h2 className="text-lg font-semibold text-gray-800 mb-3">立法成果</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <StatCard label="主提案" value={stats.bills_sponsored} unit="件" />
            <StatCard label="　うち成立" value={stats.bills_sponsored_passed} unit="件" />
            <StatCard label="　うち審議中" value={stats.bills_sponsored_pending} unit="件" />
            <StatCard label="共同提案" value={stats.bills_cosponsored} unit="件" />
          </div>

          <div className="text-xs text-gray-400">
            最終更新：{new Date(stats.updated_at).toLocaleDateString("ja-JP")}
          </div>
        </>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-sm text-yellow-800">
          この議員の統計データはまだ収集中です。
        </div>
      )}

      {/* 発議法案一覧 */}
      {memberBills.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            発議法案（直近4会期）
          </h2>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs">
                <tr>
                  <th className="px-3 py-2 text-left">会期</th>
                  <th className="px-3 py-2 text-left">法案名</th>
                  <th className="px-3 py-2 text-left">状況</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {memberBills.map((bill, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-500 whitespace-nowrap">
                      第{bill.session}回
                    </td>
                    <td className="px-3 py-2">
                      <a
                        href={bill.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-700 hover:underline"
                      >
                        {bill.name}
                      </a>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
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
          <div className="mt-1 text-xs text-gray-400">※ 主提案のみ表示（共同提案は今後対応予定）</div>
        </div>
      )}

      {/* 出典リンク */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <a
          href={kokkaiBrowseUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          国会会議録検索システムで発言記録を検索 →
        </a>
        <div className="mt-2 text-xs text-gray-400">
          データ出典：国会会議録検索システム（国立国会図書館）
        </div>
      </div>
    </main>
  );
}
