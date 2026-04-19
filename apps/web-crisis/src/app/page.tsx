import { redirect } from 'next/navigation';

/**
 * The root path redirects to /en/ as a static safe default. Static export pre-renders
 * this redirect via an HTML meta refresh + Link header, so no server-side runtime is needed.
 */
export default function RootPage() {
  redirect('/en');
}
