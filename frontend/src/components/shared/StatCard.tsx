import { Card } from '../ui/Card'

type Props = { title: string; value: string | number; accent?: 'blue' | 'green' | 'yellow' | 'red' }

const ACCENT: Record<NonNullable<Props['accent']>, string> = {
  blue: 'text-white',
  green: 'text-[#ddd]',
  yellow: 'text-[#bbb]',
  red: 'text-[#999]',
}

export function StatCard({ title, value, accent = 'blue' }: Props) {
  return (
    <Card className="p-4">
      <div className="text-xs uppercase tracking-wide text-[#555]">{title}</div>
      <div className={`mt-2 text-3xl font-semibold ${ACCENT[accent]}`}>{value}</div>
    </Card>
  )
}
