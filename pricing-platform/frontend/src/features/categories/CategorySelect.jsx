import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { useMemo } from "react";

import { useAllCategories } from "./hooks";
import { flattenCategoryTree } from "./tree";

export default function CategorySelect({
  value,
  onChange,
  label = "Category",
  required = false,
  error = false,
  helperText,
}) {
  const { data: categories, isLoading } = useAllCategories();

  const options = useMemo(() => flattenCategoryTree(categories ?? []), [categories]);
  const selected = options.find((option) => option.id === value) ?? null;

  return (
    <Autocomplete
      options={options}
      value={selected}
      loading={isLoading}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={(option) => option.name}
      onChange={(_, newValue) => onChange(newValue ? newValue.id : "")}
      renderOption={(props, option) => (
        <li {...props} key={option.id} style={{ paddingLeft: 16 + option.depth * 20 }}>
          {option.depth > 0 ? "— " : ""}
          {option.name}
        </li>
      )}
      renderInput={(params) => (
        <TextField {...params} label={label} required={required} error={error} helperText={helperText} />
      )}
    />
  );
}
