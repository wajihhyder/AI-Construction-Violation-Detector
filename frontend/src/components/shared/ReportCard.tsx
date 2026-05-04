import { format } from 'date-fns'
import { Link } from 'react-router-dom'

import type { AuthorityReportItem } from '../../types/report'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { ViolationBadge } from './ViolationBadge'

type Props = { report: AuthorityReportItem }

export function ReportCard({ report }: Props) {
  return (
    <tr className="border-b border-[#222] transition-colors hover:bg-[#0a0a0a]/80">
      <td className="px-3 py-3 font-mono text-sm">
        #{String(report.report_id).padStart(5, '0')}
      </td>
      <td className="px-3 py-3 text-sm">{report.district_location}</td>
      <td className="px-3 py-3 text-sm text-[#888]">
        {format(new Date(report.submission_date), 'MMM d, yyyy HH:mm')}
      </td>
      <td className="px-3 py-3 text-xs">{report.reporter_type}</td>
      <td className="px-3 py-3 text-xs">
        {report.input_type === null ? '—' : report.input_type ? 'Street' : 'Aerial'}
      </td>
      <td className="px-3 py-3">
        <Badge status={report.status}>{report.status.replace('_', ' ')}</Badge>
      </td>
      <td className="px-3 py-3">
        <ViolationBadge type={report.violation_type} />
      </td>
      <td className="px-3 py-3 text-right">
        <Link to={`/authority/reports/${report.report_id}`}>
          <Button variant="secondary" className="!py-1 !text-xs">
            View Details
          </Button>
        </Link>
      </td>
    </tr>
  )
}
