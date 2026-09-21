import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchImportErrors, fetchImportJob, fetchImportTemplate, startImport, uploadImport } from "./api";

const ACTIVE_STATUSES = new Set(["queued", "processing"]);

export function useUploadImport() {
  return useMutation({ mutationFn: uploadImport });
}

export function useStartImport() {
  return useMutation({ mutationFn: ({ jobId, mapping }) => startImport(jobId, mapping) });
}

// Polls while the job is queued/processing so the wizard can show live
// progress without the user refreshing the page; stops once the job
// reaches a terminal status (completed / completed_with_errors / failed).
export function useImportJob(jobId, { poll = false } = {}) {
  return useQuery({
    queryKey: ["imports", "detail", jobId],
    queryFn: () => fetchImportJob(jobId),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      if (!poll) return false;
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.has(status) ? 1500 : false;
    },
  });
}

export function useImportErrors(jobId, params) {
  return useQuery({
    queryKey: ["imports", "errors", jobId, params],
    queryFn: () => fetchImportErrors(jobId, params),
    enabled: Boolean(jobId),
  });
}

// Fetches the template then immediately triggers a browser download — a
// one-off action, not cacheable server state, hence a mutation rather than
// a query.
export function useDownloadImportTemplate() {
  return useMutation({
    mutationFn: async (entityType) => {
      const { filename, content_type, content_base64 } = await fetchImportTemplate(entityType);
      const link = document.createElement("a");
      link.href = `data:${content_type};base64,${content_base64}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
  });
}
