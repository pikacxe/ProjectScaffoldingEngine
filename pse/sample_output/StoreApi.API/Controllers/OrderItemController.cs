using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using StoreApi.API.Dtos;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OrderItemController : ControllerBase
{
    private readonly IOrderItemRepository _orderItemRepository;

    public OrderItemController(IOrderItemRepository orderItemRepository)
    {
        _orderItemRepository = orderItemRepository;
    }

    [HttpGet]
    public ActionResult<List<OrderItemDto>> GetAll()
    {
        var entities = _orderItemRepository.GetAll().Select(ToDto).ToList();
        return Ok(entities);
    }

    [HttpGet("{id}")]
    public ActionResult<OrderItemDto> GetById(Guid id)
    {
        var entity = _orderItemRepository.GetById(id);
        if (entity is null)
        {
            return NotFound();
        }

        return Ok(ToDto(entity));
    }

    [HttpPost]
    public ActionResult<OrderItemDto> Create(OrderItemDto request)
    {
        var entity = ToEntity(request);
        _orderItemRepository.Create(entity);
        return CreatedAtAction(nameof(GetById), new { id = entity.ProductId }, ToDto(entity));
    }

    [HttpPut("{id}")]
    public IActionResult Update(Guid id, OrderItemDto request)
    {
        var entity = ToEntity(request);
        entity.ProductId = id;
        _orderItemRepository.Update(entity);
        return NoContent();
    }

    [HttpDelete("{id}")]
    public IActionResult Delete(Guid id)
    {
        var existingEntity = _orderItemRepository.GetById(id);
        if (existingEntity is null)
        {
            return NotFound();
        }

        _orderItemRepository.Delete(id);
        return NoContent();
    }

    private static OrderItemDto ToDto(OrderItem entity)
    {
        return new OrderItemDto
        {
            ProductId = entity.ProductId,
            Quantity = entity.Quantity,
        };
    }

    private static OrderItem ToEntity(OrderItemDto dto)
    {
        return new OrderItem
        {
            ProductId = dto.ProductId,
            Quantity = dto.Quantity,
        };
    }
}
