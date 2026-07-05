using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using StoreApi.API.Dtos;
using StoreApi.Domain.Entities;
using StoreApi.Domain.Repositories;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OrderController : ControllerBase
{
    private readonly IOrderRepository _orderRepository;

    public OrderController(IOrderRepository orderRepository)
    {
        _orderRepository = orderRepository;
    }

    [HttpGet]
    public ActionResult<List<OrderDto>> GetAll()
    {
        var entities = _orderRepository.GetAll().Select(ToDto).ToList();
        return Ok(entities);
    }

    [HttpGet("{id}")]
    public ActionResult<OrderDto> GetById(Guid id)
    {
        var entity = _orderRepository.GetById(id);
        if (entity is null)
        {
            return NotFound();
        }

        return Ok(ToDto(entity));
    }

    [HttpPost]
    public ActionResult<OrderDto> Create(OrderDto request)
    {
        var entity = ToEntity(request);
        _orderRepository.Create(entity);
        return CreatedAtAction(nameof(GetById), new { id = entity.Id }, ToDto(entity));
    }

    [HttpPut("{id}")]
    public IActionResult Update(Guid id, OrderDto request)
    {
        var entity = ToEntity(request);
        entity.Id = id;
        _orderRepository.Update(entity);
        return NoContent();
    }

    [HttpDelete("{id}")]
    public IActionResult Delete(Guid id)
    {
        var existingEntity = _orderRepository.GetById(id);
        if (existingEntity is null)
        {
            return NotFound();
        }

        _orderRepository.Delete(id);
        return NoContent();
    }

    private static OrderDto ToDto(Order entity)
    {
        return new OrderDto
        {
            Id = entity.Id,
            CreatedAt = entity.CreatedAt,
            Status = entity.Status,
        };
    }

    private static Order ToEntity(OrderDto dto)
    {
        return new Order
        {
            Id = dto.Id,
            CreatedAt = dto.CreatedAt,
            Status = dto.Status,
        };
    }
}
