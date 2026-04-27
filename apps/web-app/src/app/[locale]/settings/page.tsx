'use client';

import { use, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useUser, useAuth, useClerk } from '@clerk/nextjs';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@disciplineos/design-system';
import { requestDataExport, requestAccountDeletion } from '@/lib/api';

const APP_VERSION = '1.0.0-beta';

// ---------------------------------------------------------------------------
// Toggle component
// ---------------------------------------------------------------------------

interface ToggleProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
}

function Toggle({ id, checked, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0">
        <label htmlFor={id} className="block text-sm font-medium text-ink-primary cursor-pointer">
          {label}
        </label>
        {description && (
          <p className="mt-0.5 text-xs text-ink-tertiary leading-snug">{description}</p>
        )}
      </div>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 focus-visible:ring-offset-2 min-h-[44px] min-w-[44px] justify-center ${
          checked ? 'bg-accent-bronze' : 'bg-border-emphasis'
        }`}
        aria-label={label}
      >
        <span
          className={`pointer-events-none h-5 w-5 rounded-full bg-white shadow-sm ring-0 transition-transform duration-base ${
            checked ? 'translate-x-2.5' : '-translate-x-2.5'
          }`}
        />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Settings section wrapper
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={`section-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <h2
        id={`section-${title.toLowerCase().replace(/\s+/g, '-')}`}
        className="mb-3 text-sm font-semibold uppercase tracking-wide text-ink-quaternary"
      >
        {title}
      </h2>
      <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
        {children}
      </Card>
    </section>
  );
}

function SettingsRow({ children }: { children: React.ReactNode }) {
  return <div className="px-5 py-4">{children}</div>;
}

// ---------------------------------------------------------------------------
// Delete account dialog
// ---------------------------------------------------------------------------

interface DeleteDialogProps {
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
  deleteError: string | null;
}

function DeleteDialog({ onClose, onConfirm, isDeleting, deleteError }: DeleteDialogProps) {
  const t = useTranslations();
  const [confirmText, setConfirmText] = useState('');
  const isConfirmed = confirmText === t('settings.sections.privacy.deleteDialogConfirmKeyword');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-surface-overlay p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-surface-secondary p-6 shadow-xl space-y-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl leading-none shrink-0" aria-hidden="true">⚠️</span>
          <div>
            <h3 id="delete-dialog-title" className="text-base font-semibold text-ink-primary">
              {t('settings.sections.privacy.deleteDialogTitle')}
            </h3>
            <p className="mt-1 text-sm text-ink-secondary leading-relaxed">
              {t('settings.sections.privacy.deleteDialogBody')}
            </p>
          </div>
        </div>

        <div>
          <label
            htmlFor="delete-confirm-input"
            className="block text-sm font-medium text-ink-secondary mb-1.5"
          >
            {t('settings.sections.privacy.deleteConfirmLabel')}
          </label>
          <input
            id="delete-confirm-input"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={t('settings.sections.privacy.deleteDialogConfirmPlaceholder')}
            autoComplete="off"
            className="w-full rounded-lg border border-border-subtle bg-surface-primary px-3 py-2.5 text-sm font-mono text-ink-primary placeholder-ink-quaternary focus:border-signal-crisis focus:bg-surface-secondary focus:outline-none focus:ring-2 focus:ring-signal-crisis/30 transition-colors"
          />
        </div>

        {deleteError !== null && (
          <p role="alert" className="text-sm text-signal-crisis">
            {deleteError}
          </p>
        )}

        <div className="flex flex-col gap-2 pt-1">
          <Button
            variant="crisis"
            size="md"
            disabled={!isConfirmed || isDeleting}
            loading={isDeleting}
            className="w-full min-h-[44px]"
            aria-disabled={!isConfirmed || isDeleting}
            onClick={() => {
              if (isConfirmed) {
                void onConfirm();
              }
            }}
          >
            {t('settings.sections.privacy.deleteConfirmButton')}
          </Button>
          <Button
            variant="ghost"
            size="md"
            className="w-full min-h-[44px]"
            onClick={onClose}
            disabled={isDeleting}
          >
            {t('common.action.cancel')}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inner component
// ---------------------------------------------------------------------------

const USE_STUBS = process.env['NEXT_PUBLIC_USE_STUBS'] === 'true';

function SettingsInner({ locale }: { locale: string }) {
  const t = useTranslations();
  const { user } = useUser();
  const { getToken } = useAuth();
  const clerk = useClerk();

  const [pushEnabled, setPushEnabled] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Download state
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(false);

  // Delete state
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [deleteAccountError, setDeleteAccountError] = useState<string | null>(null);

  async function handleDownloadData() {
    setIsDownloading(true);
    setDownloadError(false);
    try {
      if (USE_STUBS) {
        await new Promise((resolve) => setTimeout(resolve, 600));
        const stubData = { stub: true, exported_at: new Date().toISOString() };
        const blob = new Blob([JSON.stringify(stubData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'discipline-export-stub.json';
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      const token = await getToken();
      if (!token) throw new Error('Not authenticated');
      const result = await requestDataExport(token);
      const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `discipline-export-${result.export_id.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setDownloadError(true);
    } finally {
      setIsDownloading(false);
    }
  }

  async function handleDeleteAccount() {
    setIsDeletingAccount(true);
    setDeleteAccountError(null);
    try {
      if (USE_STUBS) {
        await new Promise((resolve) => setTimeout(resolve, 600));
        setShowDeleteDialog(false);
        await clerk.signOut();
        return;
      }
      const token = await getToken();
      if (!token) throw new Error('Not authenticated');
      await requestAccountDeletion(token);
      setShowDeleteDialog(false);
      await clerk.signOut();
    } catch {
      setDeleteAccountError(t('settings.sections.privacy.deleteErrorGeneric'));
    } finally {
      setIsDeletingAccount(false);
    }
  }

  return (
    <Layout locale={locale}>
      <div className="space-y-8">
        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('nav.settings')}
          </h1>
        </header>

        {/* Account section */}
        <Section title={t('settings.sections.account.title')}>
          <SettingsRow>
            <p className="text-xs font-medium text-ink-quaternary uppercase tracking-wide mb-1">
              {t('settings.sections.account.displayName')}
            </p>
            <p className="text-sm font-medium text-ink-primary">
              {user?.fullName ?? user?.firstName ?? '—'}
            </p>
          </SettingsRow>
          <SettingsRow>
            <p className="text-xs font-medium text-ink-quaternary uppercase tracking-wide mb-1">
              {t('settings.sections.account.email')}
            </p>
            <p className="text-sm text-ink-primary">
              {user?.primaryEmailAddress?.emailAddress ?? '—'}
            </p>
            <p className="mt-0.5 text-xs text-ink-quaternary">{t('settings.sections.account.emailReadOnly')}</p>
          </SettingsRow>
          <SettingsRow>
            <a
              href="https://accounts.discipline.app/user"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded min-h-[44px]"
            >
              {t('settings.sections.account.manageAccount')}
              <span aria-hidden="true">↗</span>
            </a>
          </SettingsRow>
        </Section>

        {/* Notifications section */}
        <Section title={t('settings.sections.notifications.title')}>
          <SettingsRow>
            <Toggle
              id="toggle-push"
              checked={pushEnabled}
              onChange={setPushEnabled}
              label={t('settings.sections.notifications.pushNotifications')}
              description={t('settings.sections.notifications.pushDescription')}
            />
          </SettingsRow>
          <SettingsRow>
            <Toggle
              id="toggle-email"
              checked={emailEnabled}
              onChange={setEmailEnabled}
              label={t('settings.sections.notifications.weeklyInsights')}
              description={t('settings.sections.notifications.emailDescription')}
            />
          </SettingsRow>
        </Section>

        {/* Privacy section */}
        <Section title={t('settings.sections.privacy.title')}>
          <SettingsRow>
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-ink-primary">
                {t('settings.sections.privacy.downloadData')}
              </p>
              <p className="text-xs text-ink-tertiary">{t('settings.sections.privacy.downloadDescription')}</p>
              {downloadError && (
                <p role="alert" className="text-xs text-signal-crisis mt-1">
                  {t('settings.sections.privacy.downloadErrorGeneric')}
                </p>
              )}
              <Button
                variant="secondary"
                size="sm"
                loading={isDownloading}
                disabled={isDownloading}
                className="mt-2 self-start min-h-[44px]"
                onClick={() => { void handleDownloadData(); }}
              >
                <span aria-hidden="true">⬇</span>
                {t('settings.sections.privacy.downloadData')}
              </Button>
            </div>
          </SettingsRow>
          <SettingsRow>
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-signal-crisis">
                {t('settings.sections.privacy.deleteAccount')}
              </p>
              <p className="text-xs text-ink-tertiary">{t('settings.sections.privacy.deleteDescription')}</p>
              <Button
                variant="crisis"
                size="sm"
                className="mt-2 self-start min-h-[44px]"
                onClick={() => setShowDeleteDialog(true)}
              >
                {t('common.action.delete')} {t('settings.sections.account.title').toLowerCase()}
              </Button>
            </div>
          </SettingsRow>
        </Section>

        {/* About section */}
        <Section title={t('settings.sections.about.title')}>
          <SettingsRow>
            <div className="flex items-center justify-between">
              <span className="text-sm text-ink-secondary">{t('settings.sections.about.version')}</span>
              {/* Latin digits for version numbers */}
              <span className="text-sm font-mono text-ink-quaternary tabular-nums">{APP_VERSION}</span>
            </div>
          </SettingsRow>
          <SettingsRow>
            <a
              href={`/${locale}/privacy`}
              className="block text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
            >
              {t('settings.sections.about.privacyPolicy')}
            </a>
          </SettingsRow>
          <SettingsRow>
            <a
              href={`/${locale}/terms`}
              className="block text-sm font-medium text-accent-bronze hover:text-accent-bronze/80 min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded"
            >
              {t('settings.sections.about.terms')}
            </a>
          </SettingsRow>
        </Section>
      </div>

      {/* Delete confirmation dialog — rendered outside card to sit in front of everything */}
      {showDeleteDialog && (
        <DeleteDialog
          onClose={() => {
            if (!isDeletingAccount) {
              setShowDeleteDialog(false);
              setDeleteAccountError(null);
            }
          }}
          onConfirm={handleDeleteAccount}
          isDeleting={isDeletingAccount}
          deleteError={deleteAccountError}
        />
      )}
    </Layout>
  );
}

// ---------------------------------------------------------------------------
// Page export
// ---------------------------------------------------------------------------

export default function SettingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <SettingsInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.title
 *   settings.sections.account.title / .displayName / .email / .manageAccount
 *   settings.sections.notifications.title / .pushNotifications / .weeklyInsights
 *   settings.sections.privacy.title / .downloadData / .deleteAccount
 *   settings.sections.privacy.deleteConfirmLabel / .deleteConfirmButton / .deleteWarning
 *   settings.sections.about.title / .version / .privacyPolicy / .terms
 *   common.action.delete / .cancel
 *
 *   settings.sections.account.emailReadOnly
 *   settings.sections.notifications.pushDescription
 *   settings.sections.notifications.emailDescription
 *   settings.sections.privacy.downloadDescription
 *   settings.sections.privacy.deleteDescription
 *   settings.sections.privacy.deleteDialogTitle
 *   settings.sections.privacy.deleteDialogBody
 *   settings.sections.privacy.deleteDialogConfirmPlaceholder
 *   settings.sections.privacy.deleteDialogConfirmKeyword
 *   settings.sections.privacy.downloadErrorGeneric  (new — shown inline below button)
 *   settings.sections.privacy.deleteErrorGeneric    (new — shown inside delete dialog)
 */
