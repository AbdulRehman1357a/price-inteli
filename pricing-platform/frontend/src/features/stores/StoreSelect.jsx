import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

import { useAllStores } from "./hooks";

export default function StoreSelect({
  value,
  onChange,
  label = "Store",
  required = false,
  error = false,
  helperText,
}) {
  const { data: stores, isLoading } = useAllStores();
  const options = stores ?? [];
  const selected = options.find((option) => option.id === value) ?? null;

  return (
    <Autocomplete
      options={options}
      value={selected}
      loading={isLoading}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={(option) => `${option.name} (${option.store_code})`}
      onChange={(_, newValue) => onChange(newValue ? newValue.id : "")}
      renderInput={(params) => (
        <TextField {...params} label={label} required={required} error={error} helperText={helperText} />
      )}
    />
  );
}
