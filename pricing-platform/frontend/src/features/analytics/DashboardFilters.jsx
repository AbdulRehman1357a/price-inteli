import Stack from "@mui/material/Stack";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import { useMemo } from "react";

import { flattenCategoryTree } from "../categories/tree";
import { useAllCategories } from "../categories/hooks";
import ProductSelect from "../products/ProductSelect";
import { useAllStores } from "../stores/hooks";
import { useAuth } from "../auth/AuthContext";

// Shared by every Phase 15 dashboard page. Organization is deliberately
// not a real filter control — this app is single-tenant-per-login (every
// request is already scoped to the signed-in organization), so it's shown
// as a fixed, disabled field rather than a selector with only one option.
export default function DashboardFilters({
  dateFrom,
  dateTo,
  storeId,
  categoryId,
  productId,
  onChange,
}) {
  const { organization } = useAuth();
  const { data: stores } = useAllStores();
  const { data: categories } = useAllCategories();
  const categoryOptions = useMemo(() => flattenCategoryTree(categories ?? []), [categories]);

  const current = { dateFrom, dateTo, storeId, categoryId, productId };
  const set = (field) => (value) => onChange({ ...current, [field]: value });

  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      alignItems={{ sm: "center" }}
      sx={{ mb: 3 }}
      flexWrap="wrap"
      useFlexGap
    >
      <TextField label="Organization" value={organization?.name ?? ""} disabled sx={{ minWidth: 180 }} />
      <TextField
        label="From"
        type="date"
        value={dateFrom}
        onChange={(event) => set("dateFrom")(event.target.value)}
        InputLabelProps={{ shrink: true }}
        sx={{ minWidth: 160 }}
      />
      <TextField
        label="To"
        type="date"
        value={dateTo}
        onChange={(event) => set("dateTo")(event.target.value)}
        InputLabelProps={{ shrink: true }}
        sx={{ minWidth: 160 }}
      />
      <TextField
        select
        label="Store"
        value={storeId}
        onChange={(event) => set("storeId")(event.target.value)}
        sx={{ minWidth: 180 }}
      >
        <MenuItem value="">All stores</MenuItem>
        {(stores ?? []).map((store) => (
          <MenuItem key={store.id} value={store.id}>
            {store.name}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        select
        label="Category"
        value={categoryId}
        onChange={(event) => set("categoryId")(event.target.value)}
        sx={{ minWidth: 200 }}
      >
        <MenuItem value="">All categories</MenuItem>
        {categoryOptions.map((option) => (
          <MenuItem key={option.id} value={option.id}>
            {"— ".repeat(option.depth)}
            {option.name}
          </MenuItem>
        ))}
      </TextField>
      <div style={{ minWidth: 220 }}>
        <ProductSelect value={productId} onChange={set("productId")} label="Product (all)" />
      </div>
    </Stack>
  );
}
