db.trades.aggregate([
  {
    $group: {
      _id: "$symbol",
      avg: { $avg: "$price" }
    }
  }
])