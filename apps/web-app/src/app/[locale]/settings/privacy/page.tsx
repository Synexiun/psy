'use client';

import * as React from 'react';
import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useAuth, useClerk } from '@clerk/nextjs';
import { Layout } from '@/components/Layout';
import { Button, Card } from '@disciplineos/design-system';
import { requestDataExport, requestAccountDeletion } from '@/lib/api';

// ---------------------------------------------------------------------------
// Delete account dialog
// ---------------------------------------------------------------------------

interface DeleteDialogProps {
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
  deleteError: string | null;
}

function DeleteDialog({ onClose, onConfirm, isDeleting, deleteError }: DeleteDialogProps): React.ReactElement {
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.75}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-6 w-6 text-signal-crisis shrink-0"
            aria-hidden="true"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12" y2="17.01" />
          </svg>
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

function PrivacyInner({ locale }: { locale: string }): React.ReactElement {
  const t = useTranslations();
  const { getToken } = useAuth();
  const clerk = useClerk();
  const router = useRouter();

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
      <div className="space-y-6">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb">
          <button
            type="button"
            onClick={() => router.push(`/${locale}/settings`)}
            className="inline-flex items-center gap-1.5 text-sm text-ink-tertiary hover:text-ink-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-bronze/30 rounded min-h-[44px] transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.75}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
            {t('nav.settings')}
          </button>
        </nav>

        {/* Page header */}
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-primary">
            {t('settings.sections.privacy.title')}
          </h1>
        </header>

        {/* Privacy actions */}
        <Card className="divide-y divide-border-subtle p-0 overflow-hidden">
          {/* Download data */}
          <div className="px-5 py-4">
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-ink-primary">
                {t('settings.sections.privacy.downloadData')}
              </p>
              <p className="text-xs text-ink-tertiary">
                {t('settings.sections.privacy.downloadDescription')}
              </p>
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.75}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-4 w-4"
                  aria-hidden="true"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                {t('settings.sections.privacy.downloadData')}
              </Button>
            </div>
          </div>

          {/* Delete account */}
          <div className="px-5 py-4">
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-signal-crisis">
                {t('settings.sections.privacy.deleteAccount')}
              </p>
              <p className="text-xs text-ink-tertiary">
                {t('settings.sections.privacy.deleteDescription')}
              </p>
              <Button
                variant="crisis"
                size="sm"
                className="mt-2 self-start min-h-[44px]"
                onClick={() => setShowDeleteDialog(true)}
              >
                {t('common.action.delete')} {t('settings.sections.account.title').toLowerCase()}
              </Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Delete confirmation dialog */}
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

export default function PrivacyPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  const { locale } = use(params);
  return <PrivacyInner locale={locale} />;
}

/*
 * i18n keys used from en.json:
 *   nav.settings
 *   settings.sections.privacy.title / .downloadData / .downloadDescription
 *   settings.sections.privacy.deleteAccount / .deleteDescription
 *   settings.sections.privacy.deleteDialogTitle / .deleteDialogBody
 *   settings.sections.privacy.deleteDialogConfirmPlaceholder / .deleteDialogConfirmKeyword
 *   settings.sections.privacy.deleteConfirmLabel / .deleteConfirmButton
 *   settings.sections.privacy.downloadErrorGeneric / .deleteErrorGeneric
 *   settings.sections.account.title
 *   common.action.delete / .cancel
 */
