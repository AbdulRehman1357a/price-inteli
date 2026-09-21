import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import { useCreateCategory, useUpdateCategory, useCategory } from "../features/categories/hooks";

export default function CategoryEditPage() {
  const { categoryId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(categoryId);
  const { data: category } = useCategory(categoryId);
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory(categoryId);

  const [values, setValues] = useState({ name: "", description: "" });

  // Update form values when data loads
  useState(() => {
      if (category) setValues({ name: category.name, description: category.description || "" });
  }, [category]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isEdit) {
      await updateCategory.mutateAsync(values);
    } else {
      await createCategory.mutateAsync(values);
    }
    navigate("/categories");
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        {isEdit ? "Edit Category" : "New Category"}
      </Typography>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            <TextField label="Name" value={values.name} onChange={(e) => setValues({...values, name: e.target.value})} required />
            <TextField label="Description" value={values.description} onChange={(e) => setValues({...values, description: e.target.value})} multiline rows={3} />
            <Button type="submit" variant="contained">Save</Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}
