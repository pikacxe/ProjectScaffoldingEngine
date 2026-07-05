using System;

namespace StoreApi.Domain.Entities;

public class Order
{
    public Guid Id { get; set; }
    public DateTime CreatedAt { get; set; }
    public string Status { get; set; } = string.Empty;
}
