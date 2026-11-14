const DOT = { Pending: 'bg-amber', Processing: 'bg-cobalt', Completed: 'bg-gain', Failed: 'bg-loss' }

export default function Status({ value }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm font-medium">
      <span className={'h-2 w-2 rounded-full ' + (DOT[value] || 'bg-mute')} /> {value}
    </span>
  )
}
