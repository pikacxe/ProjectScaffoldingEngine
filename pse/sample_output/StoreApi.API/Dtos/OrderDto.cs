using System;

namespace StoreApi.API.Dtos;

public class OrderDto
{
    public Guid Id { get; set; }
    public DateTime CreatedAt { get; set; }
    public string Status { get; set; } = string.Empty;
}
