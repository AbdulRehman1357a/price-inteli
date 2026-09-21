import { apiClient } from "../../api/client";

export function fetchDashboardMetrics({ dateFrom, dateTo, storeId, categoryId, productId } = {}) {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  if (storeId) params.store_id = storeId;
  if (categoryId) params.category_id = categoryId;
  if (productId) params.product_id = productId;

  return apiClient.get("/analytics/dashboard", { params }).then((res) => res.data.data);
}
