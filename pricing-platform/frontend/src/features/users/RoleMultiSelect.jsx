import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";

import { useRoles } from "../roles/hooks";

// Roles are a small, fixed catalog (the 6 seeded system roles) so this loads
// them all up front rather than searching-as-you-type like ProductMultiSelect.
export default function RoleMultiSelect({ value, onChange, error, helperText }) {
  const { data: roles = [], isLoading } = useRoles();
  const selected = roles.filter((role) => value?.includes(role.id));

  return (
    <Autocomplete
      multiple
      options={roles}
      value={selected}
      loading={isLoading}
      isOptionEqualToValue={(option, val) => option.id === val.id}
      getOptionLabel={(option) => option.name}
      onChange={(_, newValue) => onChange(newValue.map((role) => role.id))}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Roles"
          required
          error={error}
          helperText={helperText ?? "Determines which permissions this user has."}
        />
      )}
    />
  );
}
