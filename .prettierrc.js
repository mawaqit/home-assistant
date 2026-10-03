/** @type {import("prettier").Config} */
module.exports = {
  overrides: [
    {
      files: "./custom_components/**/*.json",
      options: {
        plugins: [require.resolve("prettier-plugin-sort-json")],
        jsonRecursiveSort: true,
        jsonSortOrder: JSON.stringify({ [/.*/]: "numeric" }),
      },
    },
    {
      files: ["manifest.json"],
      options: {
        // domain and name should stay at the top
        jsonSortOrder: JSON.stringify({
          domain: null,
          name: null,
          [/.*/]: "numeric",
        }),
      },
    },
  ],
};
