import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

import { useAllStores } from "../stores/hooks";
import { useChannels } from "./hooks";
import { OUTPUT_TYPE_OPTIONS } from "./options";

const typeLabel = (value) => OUTPUT_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;

export default function ChannelSelect({
  value,
  onChange,
  label = "Output Channel",
  required = false,
  error = false,
  helperText,
}) {
  const { data, isLoading } = useChannels({ page: 1, pageSize: 100 });
  const { data: stores } = useAllStores();
  const options = data?.items ?? [];
  const selected = options.find((option) => option.id === value) ?? null;
  // A channel's store is fixed on the channel itself (not chosen again per
  // dispatch), so it's surfaced here in the option label — see
  // OutputJobsPage's Dispatch Output form, which no longer asks for a store.
  const storeLabel = (storeId) => {
    if (!storeId) return "All stores";
    return stores?.find((s) => s.id === storeId)?.name ?? "Store-specific";
  };
  const optionLabel = (option) => `${option.name} (${typeLabel(option.output_type)}) — ${storeLabel(option.store_id)}`;

  return (
    <Autocomplete
      options={options}
      value={selected}
      loading={isLoading}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={optionLabel}
      onChange={(_, newValue) => onChange(newValue ? newValue.id : "")}
      renderInput={(params) => (
        <TextField {...params} label={label} required={required} error={error} helperText={helperText} />
      )}
    />
  );
}
