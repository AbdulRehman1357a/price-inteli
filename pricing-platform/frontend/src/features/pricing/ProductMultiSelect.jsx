import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { useEffect, useState } from "react";

import { useProducts } from "../products/hooks";

// Same search-as-you-type approach as features/products/ProductSelect, but
// for picking several products at once (Product Scope on a pricing rule).
export default function ProductMultiSelect({
  value,
  onChange,
  label = "Product Scope",
  helperText = "Leave empty to match any product.",
}) {
  const [inputValue, setInputValue] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => setSearch(inputValue), 300);
    return () => clearTimeout(timeout);
  }, [inputValue]);

  const { data, isLoading } = useProducts({ page: 1, pageSize: 20, search });
  const options = data?.items ?? [];
  const selected = value ?? [];

  return (
    <Autocomplete
      multiple
      options={options}
      value={selected}
      inputValue={inputValue}
      onInputChange={(_, newInputValue) => setInputValue(newInputValue)}
      loading={isLoading}
      filterOptions={(x) => x}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={(option) => `${option.product_name} (${option.sku})`}
      onChange={(_, newValue) => onChange(newValue)}
      renderInput={(params) => <TextField {...params} label={label} helperText={helperText} />}
    />
  );
}
