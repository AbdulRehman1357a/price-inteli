import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createCategory,
  deleteCategory,
  fetchAllCategories,
  fetchCategories,
  fetchCategory,
  updateCategory,
} from "./api";

const categoriesKey = (params) => ["categories", params];
const categoryKey = (id) => ["categories", "detail", id];

export function useAllCategories() {
  return useQuery({
    queryKey: ["categories", "all"],
    queryFn: fetchAllCategories,
  });
}

export function useCategories(params) {
  return useQuery({
    queryKey: categoriesKey(params),
    queryFn: () => fetchCategories(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useCategory(categoryId) {
  return useQuery({
    queryKey: categoryKey(categoryId),
    queryFn: () => fetchCategory(categoryId),
    enabled: Boolean(categoryId),
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createCategory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useUpdateCategory(categoryId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateCategory(categoryId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });
}
