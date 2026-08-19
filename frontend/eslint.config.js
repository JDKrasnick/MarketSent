import eslint from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";


export default tseslint.config(
    { ignores: ["dist"] },
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    {
        files: ["**/*.{ts,tsx}"],
        languageOptions: {
            ecmaVersion: "latest",
            globals: globals.browser,
        },
        plugins: {
            "react-hooks": reactHooks,
        },
        rules: {
            ...reactHooks.configs.flat.recommended.rules,
            "@typescript-eslint/no-explicit-any": "off",
        },
    }
);
