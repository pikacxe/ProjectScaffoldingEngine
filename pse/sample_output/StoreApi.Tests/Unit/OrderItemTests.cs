using System;
using StoreApi.Domain.Entities;
using Xunit;

namespace StoreApi.Tests.Unit;

public class OrderItemTests
{
    [Fact]
    public void CanCreateOrderItem()
    {
        var entity = new OrderItem
        {
            ProductId = Guid.NewGuid(),
            Quantity = 1,
        };

        Assert.NotEqual(Guid.Empty, entity.ProductId);
        Assert.Equal(1, entity.Quantity);
    }
}
