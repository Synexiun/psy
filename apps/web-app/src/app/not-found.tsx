export default function NotFound(): React.JSX.Element {
  return (
    <main className="mx-auto max-w-xl px-6 py-24 text-center">
      <h1 className="text-4xl font-semibold">404</h1>
      <p className="mt-4 text-[hsl(215,16%,47%)]">This page could not be found.</p>
      <a href="/" className="mt-6 inline-block underline">
        Go home
      </a>
    </main>
  );
}
