import { defineConfig } from "@neon/config/v1";

export default defineConfig({
  // PostgreSQL is always available, no need to declare it
  branch: (branch) => {
    if (branch.isDefault) {
      // Production branch: size appropriately (no protected on free plan)
      return {
        postgres: {
          computeSettings: {
            autoscalingLimitMinCu: 1,
            autoscalingLimitMaxCu: 1,
          },
        },
      };
    }
    if (!branch.exists) {
      // New non-default branches: minimum compute, auto-expire, suspend on idle
      return {
        ttl: "7d",
        postgres: {
          computeSettings: {
            autoscalingLimitMinCu: 0.25,
            autoscalingLimitMaxCu: 0.25,
            suspendTimeout: "5m",
          },
        },
      };
    }
    // Existing branch: no changes
    return {};
  },
});