import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { useEffect, useState } from "react";

import { useProduct, useProducts } from "./hooks";

// Products can be numerous, unlike stores/categories, so this searches
// server-side as the user types instead of prefetching everything.
export default function ProductSelect({
  value,
  onChange,
  label = "Product",
  required = false,
  error = false,
  helperText,
}) {
  const [inputValue, setInputValue] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => setSearch(inputValue), 300);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  const { data, isLoading } = useProducts({ page: 1, pageSize: 20, search });
  const { data: selectedProduct } = useProduct(value || undefined);

  const options = data?.items ?? [];
  // Ensure the currently-selected product shows correctly even if it isn't
  // in the latest search results (e.g. right after loading an edit form).
  const mergedOptions =
    selectedProduct && !options.some((o) => o.id === selectedProduct.id)
      ? [selectedProduct, ...options]
      : options;
  const selected = mergedOptions.find((option) => option.id === value) ?? null;

  return (
    <Autocomplete
      options={mergedOptions}
      value={selected}
      inputValue={inputValue}
      onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
      loading={isLoading}
      filterOptions={(x) => x}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={(option) => `${option.product_name} (${option.sku})`}
      onChange={(_, newValue) => onChange(newValue ? newValue.id : "")}
      renderInput={(params) => (
        <TextField {...params} label={label} required={required} error={error} helperText={helperText} />
      )}
    />
  );
}
