import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Grid from "@mui/material/Grid";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import CategorySelect from "../categories/CategorySelect";
import { CURRENCY_OPTIONS } from "../../utils/localeOptions";
import { useFetchProductFromUrl } from "./hooks";
import { PRODUCT_STATUS_OPTIONS, WEIGHT_UNIT_OPTIONS } from "./options";
import { productSchema } from "./validation";

const EMPTY_VALUES = {
  product_name: "",
  sku: "",
  barcode: "",
  category_id: "",
  brand: "",
  manufacturer: "",
  status: "active",
  cost_price: "",
  base_price: "",
  selling_price: "",
  currency: "USD",
  tax_rate: "",
  short_description: "",
  description: "",
  weight: "",
  weight_unit: "",
  product_image_url: "",
  product_url: "",
  qr_id: "",
  shelf_id: "",
};

const TABS = [
  { label: "Basic Information", fields: ["product_name", "sku", "barcode", "category_id", "brand", "manufacturer", "product_url", "qr_id", "shelf_id", "status"] },
  { label: "Pricing", fields: ["cost_price", "base_price", "selling_price", "currency", "tax_rate"] },
  { label: "Additional Details", fields: ["short_description", "description", "weight", "weight_unit"] },
  { label: "Media", fields: ["product_image_url"] },
];

function TabPanel({ active, children }) {
  return (
    <Box role="tabpanel" sx={{ display: active ? "block" : "none", pt: 3 }}>
      {children}
    </Box>
  );
}

export default function ProductForm({ defaultValues, onSubmit, submitLabel }) {
  const [activeTab, setActiveTab] = useState(0);
  const [formError, setFormError] = useState(null);

  const {
    control,
    setValue,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(productSchema),
    defaultValues: { ...EMPTY_VALUES, ...defaultValues },
  });

  const imageUrl = watch("product_image_url");
  const fetchFromUrl = useFetchProductFromUrl();
  const [fetchResult, setFetchResult] = useState(null);

  const handleFetchUrl = async () => {
    const url = watch("product_url");
    if (!url) return;
    setFetchResult(null);
    try {
      const suggestion = await fetchFromUrl.mutateAsync({ url });
      if (suggestion.error) {
        setFetchResult({ type: "error", message: suggestion.error });
        return;
      }
      const fieldsFilled = { product_url: url };
      for (const [field, value] of Object.entries(suggestion)) {
        if (value != null && field !== "url" && field !== "error") {
          setValue(field, value, { shouldValidate: false });
          fieldsFilled[field] = value;
        }
      }
      const count = Object.keys(fieldsFilled).length - 1; // subtract product_url
      setFetchResult({
        type: "success",
        message: `Filled in ${count} field${count !== 1 ? "s" : ""} from the page — review before saving.`,
      });
    } catch {
      setFetchResult({ type: "error", message: "Couldn't reach the page. Try again or fill the fields manually." });
    }
  };

  const submit = async (values) => {
    setFormError(null);
    try {
      await onSubmit(values);
    } catch (error) {
      setFormError(
        error.response?.data?.error?.message ?? "Unable to save the product. Please try again."
      );
    }
  };

  const tabHasError = (fields) => fields.some((field) => Boolean(errors[field]));

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      {formError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {formError}
        </Alert>
      )}

      <Tabs
        value={activeTab}
        onChange={(_, value) => setActiveTab(value)}
        variant="scrollable"
        scrollButtons="auto"
      >
        {TABS.map((tab, index) => (
          <Tab
            key={tab.label}
            label={tab.label}
            sx={tabHasError(tab.fields) ? { color: "error.main" } : undefined}
            id={`product-tab-${index}`}
          />
        ))}
      </Tabs>

      <TabPanel active={activeTab === 0}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Controller
              name="product_name"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Product Name"
                  required
                  fullWidth
                  error={!!errors.product_name}
                  helperText={errors.product_name?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="sku"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="SKU"
                  required
                  fullWidth
                  error={!!errors.sku}
                  helperText={errors.sku?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="barcode"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Barcode"
                  fullWidth
                  error={!!errors.barcode}
                  helperText={errors.barcode?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="category_id"
              control={control}
              render={({ field }) => (
                <CategorySelect
                  value={field.value}
                  onChange={field.onChange}
                  required
                  error={!!errors.category_id}
                  helperText={errors.category_id?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="brand"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Brand"
                  fullWidth
                  error={!!errors.brand}
                  helperText={errors.brand?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="manufacturer"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Manufacturer"
                  fullWidth
                  error={!!errors.manufacturer}
                  helperText={errors.manufacturer?.message}
                />
              )}
            />
          </Grid>

          {/* Product URL with fetch button */}
          <Grid item xs={12} sm={6}>
            <Stack direction="row" spacing={1} alignItems="flex-start">
              <Box sx={{ flex: 1 }}>
                <Controller
                  name="product_url"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Product URL"
                      placeholder="e.g. https://walmart.com/ip/..."
                      fullWidth
                      error={!!errors.product_url}
                      helperText={errors.product_url?.message ?? "Paste a retailer product page to auto-fill the fields below"}
                    />
                  )}
                />
              </Box>
              <Button
                variant="outlined"
                size="small"
                sx={{ mt: "4px", minWidth: 0, whiteSpace: "nowrap" }}
                disabled={fetchFromUrl.isPending}
                onClick={handleFetchUrl}
              >
                {fetchFromUrl.isPending ? <CircularProgress size={18} /> : "Fetch"}
              </Button>
            </Stack>
            {fetchResult && (
              <Alert severity={fetchResult.type === "success" ? "success" : "error"} sx={{ mt: 1 }}>
                {fetchResult.message}
              </Alert>
            )}
          </Grid>

          {/* QR ID */}
          <Grid item xs={12} sm={6}>
            <Controller
              name="qr_id"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="QR ID"
                  fullWidth
                  error={!!errors.qr_id}
                  helperText={errors.qr_id?.message}
                />
              )}
            />
          </Grid>

          {/* Shelf ID */}
          <Grid item xs={12} sm={6}>
            <Controller
              name="shelf_id"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Shelf ID"
                  fullWidth
                  error={!!errors.shelf_id}
                  helperText={errors.shelf_id?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="status"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Status"
                  required
                  fullWidth
                  error={!!errors.status}
                  helperText={errors.status?.message}
                >
                  {PRODUCT_STATUS_OPTIONS.map((status) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel active={activeTab === 1}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Controller
              name="cost_price"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Cost Price"
                  fullWidth
                  error={!!errors.cost_price}
                  helperText={errors.cost_price?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Controller
              name="base_price"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Base Price"
                  fullWidth
                  error={!!errors.base_price}
                  helperText={errors.base_price?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Controller
              name="selling_price"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Selling Price"
                  required
                  fullWidth
                  error={!!errors.selling_price}
                  helperText={errors.selling_price?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Controller
              name="currency"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Currency"
                  fullWidth
                  error={!!errors.currency}
                  helperText={errors.currency?.message}
                >
                  {CURRENCY_OPTIONS.map((currency) => (
                    <MenuItem key={currency} value={currency}>
                      {currency}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Controller
              name="tax_rate"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Tax Rate (%)"
                  fullWidth
                  error={!!errors.tax_rate}
                  helperText={errors.tax_rate?.message}
                />
              )}
            />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel active={activeTab === 2}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Controller
              name="short_description"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Short Description"
                  fullWidth
                  error={!!errors.short_description}
                  helperText={errors.short_description?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12}>
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Full Description"
                  fullWidth
                  multiline
                  minRows={4}
                  error={!!errors.description}
                  helperText={errors.description?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="weight"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Weight"
                  fullWidth
                  error={!!errors.weight}
                  helperText={errors.weight?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Controller
              name="weight_unit"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Weight Unit"
                  fullWidth
                  error={!!errors.weight_unit}
                  helperText={errors.weight_unit?.message}
                >
                  <MenuItem value="">—</MenuItem>
                  {WEIGHT_UNIT_OPTIONS.map((unit) => (
                    <MenuItem key={unit} value={unit}>
                      {unit}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel active={activeTab === 3}>
        <Stack spacing={2}>
          <Controller
            name="product_image_url"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                label="Product Image URL"
                fullWidth
                error={!!errors.product_image_url}
                helperText={errors.product_image_url?.message ?? "Paste a link to an image — file upload isn't implemented yet."}
              />
            )}
          />
          {imageUrl ? (
            <Avatar
              src={imageUrl}
              variant="rounded"
              sx={{ width: 160, height: 160 }}
            >
              <Typography variant="caption">No preview</Typography>
            </Avatar>
          ) : (
            <Typography color="text.secondary">No image set.</Typography>
          )}
        </Stack>
      </TabPanel>

      <Box sx={{ mt: 3 }}>
        <Button type="submit" variant="contained" size="large" disabled={isSubmitting}>
          {submitLabel}
        </Button>
      </Box>
    </Box>
  );
}
