import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createProduct,
  deleteProduct,
  fetchProduct,
  fetchProducts,
  updateProduct,
  fetchProductFromUrl,
} from "./api";

const productsKey = (params) => ["products", params];
const productKey = (id) => ["products", "detail", id];

export function useProducts(params) {
  return useQuery({
    queryKey: productsKey(params),
    queryFn: () => fetchProducts(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useProduct(productId) {
  return useQuery({
    queryKey: productKey(productId),
    queryFn: () => fetchProduct(productId),
    enabled: Boolean(productId),
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useUpdateProduct(productId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateProduct(productId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useFetchProductFromUrl() {
  return useMutation({
    mutationFn: ({ url }) => fetchProductFromUrl(url),
  });
}
