'use client';
import { libraryStubs } from '@/lib/stubs/library';
import type { LibraryCategory, LibraryArticle } from '@/lib/stubs/library';

export type { LibraryCategory, LibraryArticle };

export function useLibraryCategories(): { categories: LibraryCategory[]; isLoading: boolean } {
  return { categories: libraryStubs.categories, isLoading: false };
}

export function useLibraryCategory(
  categorySlug: string,
): { category: LibraryCategory | undefined; isLoading: boolean } {
  const category = libraryStubs.categories.find((c) => c.slug === categorySlug);
  return { category, isLoading: false };
}

export function useLibraryArticle(
  categorySlug: string,
  articleSlug: string,
): { article: LibraryArticle | undefined; category: LibraryCategory | undefined; isLoading: boolean } {
  const category = libraryStubs.categories.find((c) => c.slug === categorySlug);
  const article = category?.articles.find((a) => a.slug === articleSlug);
  return { article, category, isLoading: false };
}
