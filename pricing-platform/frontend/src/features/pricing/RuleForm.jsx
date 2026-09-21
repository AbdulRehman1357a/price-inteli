import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";

import { useAllCategories } from "../categories/hooks";
import { useAllStores } from "../stores/hooks";
import ProductMultiSelect from "./ProductMultiSelect";
import { ACTION_KIND_OPTIONS, ROUNDING_OPTIONS, RULE_STATUS_OPTIONS, RULE_TYPE_OPTIONS } from "./options";
import { ruleSchema } from "./validation";

const EMPTY_VALUES = {
  name: "",
  description: "",
  rule_type: "percentage_discount",
  priority: "100",
  status: "draft",
  approval_required: false,
  effective_from: "",
  effective_to: "",
  action_kind: "percentage_discount",
  action_value: "",
  product_ids: [],
  category_ids: [],
  store_ids: [],
  min_quantity: "",
  max_quantity: "",
  min_price: "",
  max_price: "",
  min_margin_percentage: "",
  max_discount_percentage: "",
  rounding: "",
};

// Converts the API's PricingRuleOut shape (conditions_json/actions_json/
// constraints_json blobs) into this form's flat field values. `products`
// must already contain the full objects for conditions.product_ids (the
// caller resolves those, since products aren't prefetched in bulk like
// categories/stores are).
export function ruleToFormValues(rule, { categories, stores, products }) {
  const conditions = rule.conditions_json ?? {};
  const actions = rule.actions_json ?? {};
  const constraints = rule.constraints_json ?? {};
  const actionOption = ACTION_KIND_OPTIONS.find((o) => o.value === actions.kind);

  const categoryOptions = (conditions.category_ids ?? [])
    .map((id) => (categories ?? []).find((c) => c.id === id))
    .filter(Boolean);
  const storeOptions = (conditions.store_ids ?? [])
    .map((id) => (stores ?? []).find((s) => s.id === id))
    .filter(Boolean);
  const productOptions = (conditions.product_ids ?? [])
    .map((id) => (products ?? []).find((p) => p.id === id))
    .filter(Boolean);

  return {
    ...EMPTY_VALUES,
    name: rule.name,
    description: rule.description ?? "",
    rule_type: rule.rule_type,
    priority: String(rule.priority),
    status: rule.status,
    approval_required: rule.approval_required,
    effective_from: rule.effective_from ? rule.effective_from.slice(0, 16) : "",
    effective_to: rule.effective_to ? rule.effective_to.slice(0, 16) : "",
    action_kind: actions.kind ?? "percentage_discount",
    action_value: String(actionOption ? actions[actionOption.valueField] ?? "" : ""),
    product_ids: productOptions,
    category_ids: categoryOptions,
    store_ids: storeOptions,
    min_quantity: conditions.min_quantity != null ? String(conditions.min_quantity) : "",
    max_quantity: conditions.max_quantity != null ? String(conditions.max_quantity) : "",
    min_price: constraints.min_price ?? "",
    max_price: constraints.max_price ?? "",
    min_margin_percentage: constraints.min_margin_percentage ?? "",
    max_discount_percentage: constraints.max_discount_percentage ?? "",
    rounding: constraints.rounding ?? "",
  };
}

// Converts this form's flat field values back into the API's
// PricingRuleCreate/Update shape.
function toApiPayload(values) {
  const actionOption = ACTION_KIND_OPTIONS.find((o) => o.value === values.action_kind);
  const actions_json = { kind: values.action_kind, [actionOption.valueField]: values.action_value };

  const conditions_json = {};
  const productIds = (values.product_ids ?? []).map((p) => p.id ?? p);
  const categoryIds = (values.category_ids ?? []).map((c) => c.id ?? c);
  const storeIds = (values.store_ids ?? []).map((s) => s.id ?? s);
  if (productIds.length) conditions_json.product_ids = productIds;
  if (categoryIds.length) conditions_json.category_ids = categoryIds;
  if (storeIds.length) conditions_json.store_ids = storeIds;
  if (values.min_quantity) conditions_json.min_quantity = values.min_quantity;
  if (values.max_quantity) conditions_json.max_quantity = values.max_quantity;

  const constraints_json = {};
  if (values.min_price) constraints_json.min_price = values.min_price;
  if (values.max_price) constraints_json.max_price = values.max_price;
  if (values.min_margin_percentage) constraints_json.min_margin_percentage = values.min_margin_percentage;
  if (values.max_discount_percentage) constraints_json.max_discount_percentage = values.max_discount_percentage;
  if (values.rounding) constraints_json.rounding = values.rounding;

  return {
    name: values.name,
    description: values.description || null,
    rule_type: values.rule_type,
    priority: Number(values.priority),
    status: values.status,
    approval_required: Boolean(values.approval_required),
    effective_from: values.effective_from ? new Date(values.effective_from).toISOString() : null,
    effective_to: values.effective_to ? new Date(values.effective_to).toISOString() : null,
    actions_json,
    conditions_json: Object.keys(conditions_json).length ? conditions_json : null,
    constraints_json: Object.keys(constraints_json).length ? constraints_json : null,
  };
}

export default function RuleForm({ defaultValues, onSubmit, submitLabel }) {
  const [formError, setFormError] = useState(null);
  const { data: categories } = useAllCategories();
  const { data: stores } = useAllStores();

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(ruleSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const actionKind = watch("action_kind");
  const actionOption = useMemo(
    () => ACTION_KIND_OPTIONS.find((o) => o.value === actionKind) ?? ACTION_KIND_OPTIONS[0],
    [actionKind]
  );

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(toApiPayload(values));
    } catch (error) {
      setFormError(error.response?.data?.error?.message ?? "Unable to save this rule. Please try again.");
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Stack spacing={3}>
        {formError && <Alert severity="error">{formError}</Alert>}

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Details
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Rule Name"
                    required
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <Controller
                name="priority"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Priority"
                    required
                    fullWidth
                    helperText={errors.priority?.message ?? "Lower runs first"}
                    error={!!errors.priority}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="description"
                control={control}
                render={({ field }) => <TextField {...field} label="Description" fullWidth multiline minRows={2} />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="rule_type"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Rule Type" required fullWidth error={!!errors.rule_type}>
                    {RULE_TYPE_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Status" required fullWidth>
                    {RULE_STATUS_OPTIONS.map((status) => (
                      <MenuItem key={status} value={status}>
                        {status}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Scope
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Controller
                name="product_ids"
                control={control}
                render={({ field }) => <ProductMultiSelect value={field.value} onChange={field.onChange} />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="category_ids"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    multiple
                    options={categories ?? []}
                    value={field.value}
                    isOptionEqualToValue={(o, v) => o.id === v.id}
                    getOptionLabel={(o) => o.name}
                    onChange={(_, newValue) => field.onChange(newValue)}
                    renderInput={(params) => (
                      <TextField {...params} label="Category Scope" helperText="Leave empty to match any category." />
                    )}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="store_ids"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    multiple
                    options={stores ?? []}
                    value={field.value}
                    isOptionEqualToValue={(o, v) => o.id === v.id}
                    getOptionLabel={(o) => o.name}
                    onChange={(_, newValue) => field.onChange(newValue)}
                    renderInput={(params) => (
                      <TextField {...params} label="Store Scope" helperText="Leave empty to match any store." />
                    )}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Conditions (Inventory)
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="min_quantity"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Minimum Quantity"
                    fullWidth
                    error={!!errors.min_quantity}
                    helperText={errors.min_quantity?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="max_quantity"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Maximum Quantity"
                    fullWidth
                    error={!!errors.max_quantity}
                    helperText={errors.max_quantity?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Actions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="action_kind"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Action" required fullWidth>
                    {ACTION_KIND_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="action_value"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label={actionOption.valueLabel}
                    required
                    fullWidth
                    error={!!errors.action_value}
                    helperText={errors.action_value?.message}
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Constraints
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="min_price"
                control={control}
                render={({ field }) => <TextField {...field} label="Minimum Price" fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="max_price"
                control={control}
                render={({ field }) => <TextField {...field} label="Maximum Price" fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="min_margin_percentage"
                control={control}
                render={({ field }) => <TextField {...field} label="Minimum Margin (%)" fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="max_discount_percentage"
                control={control}
                render={({ field }) => <TextField {...field} label="Maximum Discount (%)" fullWidth />}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="rounding"
                control={control}
                render={({ field }) => (
                  <TextField {...field} select label="Price Rounding" fullWidth>
                    {ROUNDING_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>
          </Grid>
        </section>

        <section>
          <Typography variant="subtitle1" gutterBottom>
            Scheduling &amp; Approval
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Controller
                name="effective_from"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Effective From"
                    type="datetime-local"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Controller
                name="effective_to"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Effective To"
                    type="datetime-local"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="approval_required"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Checkbox {...field} checked={field.value} />}
                    label="Approval required before this rule's prices are applied"
                  />
                )}
              />
            </Grid>
          </Grid>
        </section>

        <Box>
          <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </Box>
      </Stack>
    </Box>
  );
}
