db.trades.aggregate([
  {
    $group: {
      _id: "$symbol",
      avg: { $avg: "$price" }
    }
  }
])

db.quotes.aggregate([
  {
    $addFields: {
      sum_price: { $add: ['$ask_price', '$bid_price'] }
    }
  },
  {
    $addFields: {
      mid_price: { $multiply: ["$sum_price", 0.5] }
    }
  },
  {
    $group: {
      _id: "$symbol",
      avg: { $avg: "$mid_price"}
    }
  }
])