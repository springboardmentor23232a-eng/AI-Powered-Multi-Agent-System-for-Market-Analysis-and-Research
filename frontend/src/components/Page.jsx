export default function Page({ title, aside, children }) {
  return (
    <div className="mx-auto max-w-5xl px-6 py-10 sm:px-10 lg:py-14">
      {title && (
        <div className="mb-10 flex flex-wrap items-end justify-between gap-3">
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
          {aside && <p className="pb-1.5 text-mute">{aside}</p>}
        </div>
      )}
      {children}
    </div>
  )
}
