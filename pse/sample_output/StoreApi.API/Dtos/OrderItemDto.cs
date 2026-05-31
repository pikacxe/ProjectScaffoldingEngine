using System;

namespace StoreApi.API.Dtos;

public class OrderItemDto
{
    public Guid ProductId { get; set; }
    public int Quantity { get; set; }
}
