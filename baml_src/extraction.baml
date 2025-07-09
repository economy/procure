/// BAML types for procurement analysis.
/// Defines the structure for a technology tool, its features, and pricing information.

class Feature {
  name string
  description string
}

class Pricing {
  tier string
  price float
  usage_limits string
}

class Tool {
  name string
  description string
  is_open_source bool
  deployment_model string
  features Feature[]
  pricing Pricing[]
  target_market string
  maturity string
  community_size string
} 