export default function RootLayout({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
