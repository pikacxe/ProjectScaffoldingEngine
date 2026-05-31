using System;

namespace StoreApi.Domain.Entities;

public class OrderItem
{
    public Guid ProductId { get; set; }
    public int Quantity { get; set; }
}
