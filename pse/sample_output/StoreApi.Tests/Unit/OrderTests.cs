using System;
using StoreApi.Domain.Entities;
using Xunit;

namespace StoreApi.Tests.Unit;

public class OrderTests
{
    [Fact]
    public void CanCreateOrder()
    {
        var entity = new Order
        {
            Id = Guid.NewGuid(),
            CreatedAt = DateTime.UtcNow,
            Status = "Status",
        };

        Assert.NotEqual(Guid.Empty, entity.Id);
        Assert.NotEqual(default, entity.CreatedAt);
        Assert.Equal("Status", entity.Status);
    }
}
