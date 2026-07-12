using System.Collections.Generic;
using StoreApi.Domain.Entities;

namespace StoreApi.Domain.Aggregates;

public class OrderAggregate
{
    public Order Root { get; }
    public List<OrderItem> OrderItems { get; } = new();

    public OrderAggregate(Order root)
    {
        Root = root;
    }
}
