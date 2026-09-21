import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createUser, deleteUser, fetchUser, fetchUsers, updateUser } from "./api";

const usersKey = (params) => ["users", params];
const userKey = (id) => ["users", "detail", id];

export function useUsers(params) {
  return useQuery({
    queryKey: usersKey(params),
    queryFn: () => fetchUsers(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useUser(userId) {
  return useQuery({
    queryKey: userKey(userId),
    queryFn: () => fetchUser(userId),
    enabled: Boolean(userId),
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useUpdateUser(userId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => updateUser(userId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
